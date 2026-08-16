"""Tests for solver failure diagnostics."""

import logging
import math
from typing import Any

from highspy import Highs, HighsStatus
import numpy as np
import pytest

from custom_components.haeo.core.model import Network, diagnostics


def _infeasible_network() -> Network:
    """Build a network that is provably infeasible.

    ``mid`` is neither a source nor a sink, so its energy balance is strict.
    Forcing 5 kW in and 2 kW out cannot be satisfied.
    """
    network = Network(name="demo", periods=np.array([1.0]))
    network.add({"element_type": "node", "name": "src", "is_source": True, "is_sink": False})
    network.add({"element_type": "node", "name": "mid", "is_source": False, "is_sink": False})
    network.add({"element_type": "node", "name": "dst", "is_source": False, "is_sink": True})

    for name, source, target, limit in (
        ("feed", "src", "mid", 5.0),
        ("drain", "mid", "dst", 2.0),
    ):
        network.add(
            {
                "element_type": "connection",
                "name": name,
                "source": source,
                "target": target,
                "tags": {1},
                "segments": {
                    "limit": {"segment_type": "power_limit", "max_power": limit, "fixed": True},
                    "pricing": {"segment_type": "pricing", "price": 0.10},
                },
            }
        )
    return network


def _feasible_network() -> Network:
    """Build a small network that solves cleanly."""
    network = Network(name="demo", periods=np.array([1.0]))
    network.add({"element_type": "node", "name": "src", "is_source": True, "is_sink": False})
    network.add({"element_type": "node", "name": "dst", "is_source": False, "is_sink": True})
    network.add(
        {
            "element_type": "connection",
            "name": "conn",
            "source": "src",
            "target": "dst",
            "tags": {1},
            "segments": {
                "limit": {"segment_type": "power_limit", "max_power": 5.0, "fixed": True},
                "pricing": {"segment_type": "pricing", "price": 0.10},
            },
        }
    )
    return network


def test_conflicting_constraints_are_named() -> None:
    """An infeasible solve names the conflicting rows in network terms."""
    network = _infeasible_network()

    with pytest.raises(ValueError, match="Optimization failed with status: Infeasible") as excinfo:
        network.optimize()

    message = str(excinfo.value)
    assert "mid.element_power_balance" in message
    assert "feed.feed_limit_power_limit" in message
    assert "drain.drain_limit_power_limit" in message


def test_irrelevant_constraints_are_excluded() -> None:
    """The reported subsystem is irreducible, not the whole model."""
    network = _infeasible_network()
    solver = network._solver

    with pytest.raises(ValueError, match="Infeasible") as excinfo:
        network.optimize()

    # The model has more rows than the conflict, so the report must be smaller.
    reported = str(excinfo.value).count("bound)")
    assert 0 < reported < int(solver.numConstrs)


def test_row_names_cover_element_constraints() -> None:
    """Row indices map back to element and constraint names."""
    network = _feasible_network()
    network.optimize()

    names = diagnostics.constraint_row_names(network)

    assert names
    assert any(label.startswith("conn.") for label in names.values())
    assert all(isinstance(index, int) for index in names)


def test_lex_row_is_labelled() -> None:
    """The lexicographic bound row is identified rather than left as a bare index."""
    network = _feasible_network()
    network.optimize()

    if network._lex_constraint is None:
        pytest.skip("no lexicographic row installed for this configuration")

    names = diagnostics.constraint_row_names(network)
    assert diagnostics.LEX_ROW_LABEL in names.values()


def test_iis_strategy_is_restored() -> None:
    """Computing an IIS leaves no lingering solver option change."""
    network = _infeasible_network()
    solver = network._solver

    _, before = solver.getOptionValue(diagnostics.IIS_STRATEGY_OPTION)

    with pytest.raises(ValueError, match="Infeasible"):
        network.optimize()

    status, after = solver.getOptionValue(diagnostics.IIS_STRATEGY_OPTION)
    assert status == HighsStatus.kOk
    assert after == before


def test_solve_counter_tracks_completed_solves() -> None:
    """A successful solve increments the reuse counter."""
    network = _feasible_network()
    assert network.solves_since_build == 0

    network.optimize()
    assert network.solves_since_build == 1

    network.optimize()
    assert network.solves_since_build == 2


def test_reused_model_failure_points_at_model_state() -> None:
    """A failure after prior solves is reported as suspect model state."""
    report = diagnostics.SolveDiagnostics(
        phase="lex secondary",
        status="Infeasible",
        n_rows=100,
        n_cols=80,
        solves_since_build=42,
        lex_row_installed=True,
        conflicts=(),
        iis_truncated=False,
        iis_note=None,
    )

    assert report.model_is_reused
    message = report.as_log_message()
    assert "42 prior solve(s)" in message
    assert "reload" in message


def test_fresh_model_failure_points_at_inputs() -> None:
    """A failure with no prior solves is attributed to the inputs."""
    report = diagnostics.SolveDiagnostics(
        phase="lex primary",
        status="Infeasible",
        n_rows=10,
        n_cols=8,
        solves_since_build=0,
        lex_row_installed=False,
        conflicts=(),
        iis_truncated=False,
        iis_note=None,
    )

    assert not report.model_is_reused
    assert "inherent to the current inputs" in report.as_log_message()


def test_unavailable_conflicts_are_explained() -> None:
    """When no IIS is available the report says why."""
    report = diagnostics.SolveDiagnostics(
        phase="blended",
        status="Unbounded",
        n_rows=5,
        n_cols=5,
        solves_since_build=1,
        lex_row_installed=False,
        conflicts=(),
        iis_truncated=False,
        iis_note="solver returned no valid IIS",
    )

    assert "unavailable (solver returned no valid IIS)" in report.as_log_message()


def test_coefficient_stats_summarise_magnitudes() -> None:
    """Coefficient statistics capture the magnitude spread that breaks rows."""
    solver = Highs()
    solver.setOptionValue("output_flag", False)
    x = solver.addVariable(lb=0, ub=1)
    y = solver.addVariable(lb=0, ub=1)

    stats = diagnostics.coefficient_stats(1e-13 * x + 5.0 * y <= 1.0)

    assert stats is not None
    assert stats.count == 2
    assert stats.min_abs == pytest.approx(1e-13)
    assert stats.max_abs == pytest.approx(5.0)
    assert stats.dynamic_range > 1e12
    assert stats.non_finite == 0
    assert "NON-FINITE" not in str(stats)


def test_coefficient_stats_ignore_exact_zeros() -> None:
    """Exact zero coefficients carry no information and are not counted."""
    solver = Highs()
    solver.setOptionValue("output_flag", False)
    x = solver.addVariable(lb=0, ub=1)
    y = solver.addVariable(lb=0, ub=1)

    stats = diagnostics.coefficient_stats(0.0 * x + 2.0 * y <= 1.0)

    assert stats is not None
    assert stats.count == 1
    assert stats.min_abs == pytest.approx(2.0)


def test_coefficient_stats_handle_unreadable_expression() -> None:
    """An expression that cannot be read yields None rather than raising."""

    class Broken:
        def unique_elements(self) -> tuple[Any, Any]:
            msg = "cannot read"
            raise RuntimeError(msg)

    assert diagnostics.coefficient_stats(Broken()) is None  # type: ignore[arg-type]


def test_empty_coefficients_report_infinite_range() -> None:
    """A row with no non-zero coefficients reports an infinite dynamic range."""
    stats = diagnostics.CoefficientStats(count=0, min_abs=0.0, max_abs=0.0, non_finite=0)
    assert math.isinf(stats.dynamic_range)


def test_collect_survives_a_broken_network(caplog: pytest.LogCaptureFixture) -> None:
    """Diagnostics never raise, even when the network cannot be inspected."""

    class BrokenNetwork:
        solves_since_build = 3

        def constraints(self) -> dict[str, Any]:
            msg = "constraints unavailable"
            raise RuntimeError(msg)

    solver = Highs()
    solver.setOptionValue("output_flag", False)

    with caplog.at_level(logging.DEBUG):
        report = diagnostics.collect(
            solver,
            phase="lex primary",
            status="Infeasible",
            network=BrokenNetwork(),  # type: ignore[arg-type]
        )

    assert report.solves_since_build == 3
    assert report.conflicts == ()


def test_reported_conflicts_are_capped() -> None:
    """A pathological subsystem cannot flood the log."""
    conflicts = tuple(f"row[{i}]" for i in range(diagnostics.MAX_REPORTED_ROWS))
    report = diagnostics.SolveDiagnostics(
        phase="lex primary",
        status="Infeasible",
        n_rows=9999,
        n_cols=9999,
        solves_since_build=0,
        lex_row_installed=False,
        conflicts=conflicts,
        iis_truncated=True,
        iis_note=None,
    )

    message = report.as_log_message()
    assert message.rstrip().endswith("...")
    assert len(report.conflicts) == diagnostics.MAX_REPORTED_ROWS

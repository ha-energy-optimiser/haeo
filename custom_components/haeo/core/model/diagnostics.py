"""Structured diagnostics for solver failures.

A bare ``Infeasible`` status carries no information about which constraints
conflict, whether the failure is inherent to the inputs, or whether it is an
artefact of a reused solver model. This module turns a failed solve into a
report that names the conflicting constraints in network terms and records the
state needed to tell those cases apart.

All collection is best effort: a diagnostic must never replace or mask the
solver failure it is describing.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import math
from typing import TYPE_CHECKING, Any

from highspy import HighsIis, HighsStatus, IisBoundStatus, IisStrategy
import numpy as np

if TYPE_CHECKING:
    from highspy import Highs, highs_linear_expression

    from .network import Network

_LOGGER = logging.getLogger(__name__)

IIS_STRATEGY_OPTION = "iis_strategy"

# Cap the reported subsystem so a pathological model cannot flood the log.
MAX_REPORTED_ROWS = 20

_BOUND_LABELS = {
    int(IisBoundStatus.kIisBoundStatusLower): "lower",
    int(IisBoundStatus.kIisBoundStatusUpper): "upper",
    int(IisBoundStatus.kIisBoundStatusBoxed): "boxed",
    int(IisBoundStatus.kIisBoundStatusFree): "free",
}

LEX_ROW_LABEL = "<lexicographic objective bound>"


@dataclass(frozen=True, slots=True)
class CoefficientStats:
    """Magnitude summary of a constraint row's non-zero coefficients."""

    count: int
    min_abs: float
    max_abs: float
    non_finite: int

    @property
    def dynamic_range(self) -> float:
        """Ratio of largest to smallest non-zero magnitude."""
        if self.min_abs <= 0.0 or not math.isfinite(self.max_abs):
            return math.inf
        return self.max_abs / self.min_abs

    def __str__(self) -> str:
        """Render a compact single-line summary."""
        parts = [
            f"{self.count} non-zero",
            f"|coef| {self.min_abs:.3e}..{self.max_abs:.3e}",
            f"range {self.dynamic_range:.3e}",
        ]
        if self.non_finite:
            parts.append(f"{self.non_finite} NON-FINITE")
        return ", ".join(parts)


@dataclass(frozen=True, slots=True)
class SolveDiagnostics:
    """A structured account of one failed solve."""

    phase: str
    status: str
    n_rows: int
    n_cols: int
    solves_since_build: int
    lex_row_installed: bool
    conflicts: tuple[str, ...]
    iis_truncated: bool
    iis_note: str | None

    @property
    def model_is_reused(self) -> bool:
        """Whether this failure occurred on a model that had already solved."""
        return self.solves_since_build > 0

    def as_log_message(self) -> str:
        """Render a multi-line operator-facing report."""
        lines = [
            f"Solver failure in phase '{self.phase}': {self.status}",
            f"  model: {self.n_rows} rows x {self.n_cols} cols, "
            f"lex row {'installed' if self.lex_row_installed else 'absent'}",
        ]

        if self.model_is_reused:
            lines.append(
                f"  reuse: {self.solves_since_build} prior solve(s) on this model — "
                "if the inputs are satisfiable, the model state is suspect and a "
                "rebuild or config-entry reload should clear it",
            )
        else:
            lines.append(
                "  reuse: none, this model has not solved before — "
                "the failure is most likely inherent to the current inputs",
            )

        if self.conflicts:
            shown = ", ".join(self.conflicts)
            suffix = ", ..." if self.iis_truncated else ""
            lines.append(f"  conflicting constraints ({len(self.conflicts)}): {shown}{suffix}")
        elif self.iis_note:
            lines.append(f"  conflicting constraints: unavailable ({self.iis_note})")

        return "\n".join(lines)

    def as_exception_detail(self) -> str:
        """Render a single-line summary suitable for appending to an error message."""
        detail = (
            f"phase={self.phase}, rows={self.n_rows}, cols={self.n_cols}, solves_since_build={self.solves_since_build}"
        )
        if self.conflicts:
            shown = ", ".join(self.conflicts)
            if self.iis_truncated:
                shown += ", ..."
            detail += f", conflicts=[{shown}]"
        return detail


def coefficient_stats(expr: highs_linear_expression) -> CoefficientStats | None:
    """Summarise the coefficient magnitudes of ``expr``, or None if unavailable."""
    try:
        _, values = expr.unique_elements()
        values = np.asarray(values, dtype=float)
    except Exception:
        _LOGGER.debug("Unable to read constraint coefficients for diagnostics", exc_info=True)
        return None

    finite = values[np.isfinite(values)]
    non_finite = int(values.size - finite.size)
    nonzero = np.abs(finite[finite != 0.0])

    if nonzero.size == 0:
        return CoefficientStats(count=0, min_abs=0.0, max_abs=0.0, non_finite=non_finite)

    return CoefficientStats(
        count=int(nonzero.size),
        min_abs=float(np.min(nonzero)),
        max_abs=float(np.max(nonzero)),
        non_finite=non_finite,
    )


def constraint_row_names(network: Network) -> dict[int, str]:
    """Map solver row indices to ``element.constraint[period]`` labels."""
    names: dict[int, str] = {}

    try:
        grouped = network.constraints()
    except Exception:
        _LOGGER.debug("Unable to enumerate constraints for diagnostics", exc_info=True)
        return names

    for element_name, constraints in grouped.items():
        for constraint_name, entry in constraints.items():
            rows = entry if isinstance(entry, list) else [entry]
            for position, row in enumerate(rows):
                index = getattr(row, "index", None)
                if index is None:
                    continue
                label = f"{element_name}.{constraint_name}"
                if len(rows) > 1:
                    label = f"{label}[{position}]"
                names[int(index)] = label

    lex_row = getattr(network, "_lex_constraint", None)
    lex_index = getattr(lex_row, "index", None)
    if lex_index is not None:
        names[int(lex_index)] = LEX_ROW_LABEL

    return names


def _describe_row(index: int, bound: int, row_names: dict[int, str]) -> str:
    """Label one IIS row, including which bound is binding."""
    label = row_names.get(index, f"row[{index}]")
    bound_label = _BOUND_LABELS.get(int(bound))
    return f"{label} ({bound_label} bound)" if bound_label else label


def compute_conflicts(
    solver: Highs,
    row_names: dict[int, str],
) -> tuple[tuple[str, ...], bool, str | None]:
    """Compute an irreducible infeasible subsystem and name its rows.

    Returns the labels, whether the list was truncated, and a note explaining
    any failure to obtain one. The IIS strategy is enabled only for this call
    and restored afterwards, so a healthy solve pays nothing for it.
    """
    previous: Any = None
    restore = False

    try:
        status, previous = solver.getOptionValue(IIS_STRATEGY_OPTION)
        if status != HighsStatus.kOk:
            return (), False, "could not read iis_strategy"

        strategy = int(IisStrategy.kIisStrategyFromLpRowPriority)
        if solver.setOptionValue(IIS_STRATEGY_OPTION, strategy) != HighsStatus.kOk:
            return (), False, "could not enable iis_strategy"
        restore = True

        iis = HighsIis()
        if solver.getIis(iis) != HighsStatus.kOk:
            return (), False, "solver declined to compute an IIS"

        if not iis.valid:
            return (), False, "solver returned no valid IIS"

        indices = list(iis.row_index)
        bounds = list(iis.row_bound)
        truncated = len(indices) > MAX_REPORTED_ROWS

        labels = tuple(
            _describe_row(index, bound, row_names)
            for index, bound in zip(indices[:MAX_REPORTED_ROWS], bounds[:MAX_REPORTED_ROWS], strict=False)
        )
    except Exception as err:
        _LOGGER.debug("IIS computation failed", exc_info=True)
        return (), False, f"{type(err).__name__}"
    else:
        return labels, truncated, None
    finally:
        if restore and previous is not None:
            try:
                solver.setOptionValue(IIS_STRATEGY_OPTION, int(previous))
            except Exception:
                _LOGGER.debug("Unable to restore iis_strategy", exc_info=True)


def collect(
    solver: Highs,
    *,
    phase: str,
    status: str,
    network: Network | None = None,
    with_conflicts: bool = True,
) -> SolveDiagnostics:
    """Gather diagnostics for a failed solve. Never raises."""
    try:
        n_rows = int(solver.numConstrs)
        n_cols = int(solver.numVariables)
    except Exception:
        n_rows = n_cols = -1

    solves_since_build = int(getattr(network, "solves_since_build", 0) or 0)
    lex_row_installed = getattr(network, "_lex_constraint", None) is not None

    conflicts: tuple[str, ...] = ()
    truncated = False
    note: str | None = None

    if with_conflicts:
        row_names = constraint_row_names(network) if network is not None else {}
        conflicts, truncated, note = compute_conflicts(solver, row_names)

    return SolveDiagnostics(
        phase=phase,
        status=status,
        n_rows=n_rows,
        n_cols=n_cols,
        solves_since_build=solves_since_build,
        lex_row_installed=lex_row_installed,
        conflicts=conflicts,
        iis_truncated=truncated,
        iis_note=note,
    )

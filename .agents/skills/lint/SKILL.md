---
name: lint
description: Run every CI gate locally — ruff lint and format, pyright, import boundaries, mdformat, prettier, version consistency, unit tests, scenario tests, frontend card checks — and fix whatever fails. Use before committing, before opening a pull request, when asked to lint, format, type check, verify, or make CI pass, and when diagnosing a red CI run.
---

# Lint, format, and type check

`./tools/check.sh` runs every job from `.github/workflows/ci.yml` that can run locally, in cheapest-first order.
Use it rather than invoking the tools one at a time.

## Step 1: run the gates

```bash
./tools/check.sh          # all gates, ~65s
./tools/check.sh --fast   # ruff, pyright, unit tests only, ~35s
```

It prints one line per gate with timing, shows output only for failures, and exits non-zero if anything failed.
`hassfest` and HACS validation have no local equivalent and run only as GitHub Actions.

The script bootstraps two setup steps that are easy to miss:
the repo-root `npm ci` that prettier needs for `prettier-plugin-sort-json`,
and the frontend card build that scenario tests need to render topology SVGs.

## Step 2: fix what failed

Apply the mechanical fixes first:

```bash
./tools/check.sh --fix
```

This runs `ruff check --fix-only`, `ruff format`, `mdformat`, and `prettier --write`, then re-checks.
Everything still failing needs a real change:

- **Ruff lint**: restructure the code so the rule is satisfied naturally.
    `# noqa` is a last resort and must carry a parenthesized reason.
    See the `python` skill.
- **Pyright**: strict mode. `typing.cast` is a banned API — fix the types or use a `TypeGuard`.
    A `# type: ignore` needs a written explanation of why nothing else worked.
- **Import boundaries**: `custom_components/haeo/core/**` may import only `highspy`, `numpy`, and `typing_extensions`.
    A broken contract means the import belongs on the Home Assistant side of the boundary.
- **Tests**: `filterwarnings = ["error"]`, so a new warning is a hard failure, and `timeout = 5` turns a hang into a timeout.
- **Scenario tests**: a diff means optimizer behavior changed.
    Confirm that is intended before regenerating with `--snapshot-update`.
- **Version consistency**: `pyproject.toml` and `custom_components/haeo/manifest.json` versions must match,
    and `homeassistant>=X` in `pyproject.toml` must equal `homeassistant` in `hacs.json`.
    Run `uv sync` after changing either.

The main branch is always clean, so any failure belongs to the current branch and must be fixed rather than worked around.

## Step 3: report

Summarize which gates failed, what changed to fix them, and confirm a clean run.
Coverage is not part of this workflow — codecov enforces it on changed lines, and `/coverage` covers that.

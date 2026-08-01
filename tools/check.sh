#!/usr/bin/env bash
# Run HAEO's CI gates locally.
#
# Mirrors the jobs in .github/workflows/ci.yml so a green run here means a green
# "CI passed" check, minus hassfest/HACS which only run as GitHub Actions.
#
# Usage:
#   ./tools/check.sh              # every runnable gate (~65s)
#   ./tools/check.sh --fix        # apply formatter autofixes first, then check
#   ./tools/check.sh --fast       # ruff + pyright + unit tests only (~35s)
#   ./tools/check.sh ruff pyright # run only the named gates
#
# Gates: ruff-format ruff-lint pyright imports mdformat prettier version
#        test scenario frontend
set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

FIX=0
FAST=0
SELECTED=()

for arg in "$@"; do
  case "$arg" in
    --fix) FIX=1 ;;
    --fast) FAST=1 ;;
    --help | -h) awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"; exit 0 ;;
    -*) echo "unknown flag: $arg" >&2; exit 2 ;;
    *) SELECTED+=("$arg") ;;
  esac
done

if [[ $FAST -eq 1 && ${#SELECTED[@]} -eq 0 ]]; then
  SELECTED=(ruff-lint ruff-format pyright test)
fi

selected() {
  [[ ${#SELECTED[@]} -eq 0 ]] && return 0
  local want
  for want in "${SELECTED[@]}"; do
    [[ "$1" == *"$want"* ]] && return 0
  done
  return 1
}

FAILED=()
PASSED=()
SKIPPED=()

# run <gate-name> <command...>
run() {
  local name="$1"; shift
  selected "$name" || { SKIPPED+=("$name"); return 0; }

  local start out status
  start=$SECONDS
  out=$("$@" 2>&1)
  status=$?
  local elapsed=$((SECONDS - start))

  if [[ $status -eq 0 ]]; then
    PASSED+=("$name (${elapsed}s)")
    printf '\033[32m✓\033[0m %-14s %ss\n' "$name" "$elapsed"
  else
    FAILED+=("$name")
    printf '\033[31m✗\033[0m %-14s %ss\n' "$name" "$elapsed"
    printf '%s\n\n' "$out" | sed 's/^/    /'
  fi
}

# Tracked markdown, skipping entries deleted locally but not yet staged. On a
# clean CI checkout every tracked file exists, so this matches the CI command.
md_files() {
  git ls-files '*.md' '*.mdx' | while IFS= read -r f; do [[ -e "$f" ]] && printf '%s\n' "$f"; done
}

# Root node_modules provides prettier + prettier-plugin-sort-json. Without it
# prettier aborts with "Cannot find package 'prettier-plugin-sort-json'".
ensure_npm_root() { [[ -d node_modules ]] || npm ci --silent; }

# Scenario tests render topology SVGs through the card's export script, which
# must be built first or every scenario fails with "Card export script not found".
ensure_card_build() {
  [[ -d frontend/haeo-forecast-card/node_modules ]] || npm --prefix frontend/haeo-forecast-card ci --silent
  [[ -f frontend/haeo-forecast-card/dist/render-topology-svg.mjs ]] \
    || npm --prefix frontend/haeo-forecast-card run build --silent
}

check_versions() {
  local pyproject manifest ha_dep hacs_ha
  pyproject=$(uv run --quiet python -c \
    "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
  manifest=$(uv run --quiet python -c \
    "import json;print(json.load(open('custom_components/haeo/manifest.json'))['version'])")
  ha_dep=$(uv run --quiet python -c \
    "import tomllib,re;d=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies'];print(re.search(r'homeassistant>=(\d+\.\d+\.\d+)',str(d)).group(1))")
  hacs_ha=$(uv run --quiet python -c \
    "import json;print(json.load(open('hacs.json'))['homeassistant'])")

  local ok=0
  [[ "$pyproject" == "$manifest" ]] || {
    echo "pyproject.toml version ($pyproject) != manifest.json version ($manifest)"; ok=1; }
  [[ "$ha_dep" == "$hacs_ha" ]] || {
    echo "pyproject homeassistant>=$ha_dep != hacs.json homeassistant $hacs_ha"; ok=1; }
  return $ok
}

if [[ $FIX -eq 1 ]]; then
  echo "── applying autofixes ──"
  uv run ruff check --fix-only --quiet
  uv run ruff format --quiet
  # shellcheck disable=SC2046 # word splitting is how the file list is passed
  uv run mdformat $(md_files) >/dev/null
  ensure_npm_root && npx prettier@3 --write --log-level warn . >/dev/null
  echo
fi

echo "── gates ──"
run ruff-lint    uv run ruff check
run ruff-format  uv run ruff format --check
run imports      uv run lint-imports
# shellcheck disable=SC2046 # word splitting is how the file list is passed
run mdformat     uv run mdformat --check $(md_files)

if selected prettier; then ensure_npm_root; fi
run prettier     npx prettier@3 --check .

run version      check_versions
run pyright      uv run pyright
run test         uv run pytest -m "not guide and not scenario and not benchmark" -q --no-header

if selected scenario || selected frontend; then ensure_card_build; fi
run scenario     uv run pytest -m scenario -q --no-header
run frontend     npm --prefix frontend/haeo-forecast-card run check

echo
if [[ ${#FAILED[@]} -gt 0 ]]; then
  printf '\033[31mFAILED:\033[0m %s\n' "${FAILED[*]}"
  echo "(hassfest and HACS validation only run in GitHub Actions)"
  exit 1
fi
printf '\033[32mAll %d gates passed.\033[0m\n' "${#PASSED[@]}"
[[ ${#SKIPPED[@]} -gt 0 ]] && echo "skipped: ${SKIPPED[*]}"
echo "(hassfest and HACS validation only run in GitHub Actions)"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_FILE="$(mktemp "${TMPDIR:-/tmp}/ifind-skill-state.XXXXXX.json")"
INSTALL_TARGET="${OPENCLAW_SKILL_DIR:-$HOME/.openclaw/workspace/skills/tonghuashun-ifind-skill}"
UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/tonghuashun-ifind-skill-uv-cache}"

cleanup() {
  rm -f "${STATE_FILE}"
}
trap cleanup EXIT

cd "${ROOT_DIR}"

mkdir -p "${UV_CACHE_DIR}"
export UV_CACHE_DIR

uv run pytest -q

uv run python tonghuashun-ifind-skill/scripts/ifind_cli.py \
  --state-path "${STATE_FILE}" \
  auth-set-tokens \
  --access-token "demo-access-token" \
  --refresh-token "demo-refresh-token" >/dev/null

printf 'Validation ok\n'
printf 'OpenClaw install target: %s\n' "${INSTALL_TARGET}"

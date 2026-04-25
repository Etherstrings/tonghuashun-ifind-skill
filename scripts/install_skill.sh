#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${ROOT_DIR}/tonghuashun-ifind-skill"
TARGET_DIR="${OPENCLAW_SKILL_DIR:-$HOME/.openclaw/workspace/skills/tonghuashun-ifind-skill}"

mkdir -p "$(dirname "${TARGET_DIR}")"
rm -rf "${TARGET_DIR}"
cp -R "${SOURCE_DIR}" "${TARGET_DIR}"

printf 'Installed skill to %s\n' "${TARGET_DIR}"

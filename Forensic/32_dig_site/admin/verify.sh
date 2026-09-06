#!/usr/bin/env bash
# dig_site — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, runs the reference solve
# against a fresh copy, and checks the recovered flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{g1t_fck_r3m3mb3rs_wh4t_br4nch3s_f0rg3t_d64b02}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/make_handout.py >/dev/null
unzip -q handout/skills_archive.zip -d "$TMP"

OUT="$(python3 admin/solve.py "$TMP/skills_archive")"
echo "$OUT"

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

#!/usr/bin/env bash
# q3_numbers — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, runs the reference solve
# against a fresh copy, and checks the recovered flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{h1dd3n_r0ws_c4nt_h1d3_f0r3v3r_b7f2e9}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/make_handout.py >/dev/null
cp handout/Q3_numbers.xlsx "$TMP/Q3_numbers.xlsx"

OUT="$(python3 admin/solve.py "$TMP/Q3_numbers.xlsx")"
echo "$OUT"

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

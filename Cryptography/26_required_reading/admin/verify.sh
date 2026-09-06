#!/usr/bin/env bash
# required_reading — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, solves a fresh copy, checks flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{r34d_th3_h4ndb00k_c0v3r_t0_c0v3r_2b8d0e}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/make_handout.py >/dev/null
cp -r handout "$TMP/handout"

OUT="$(python3 admin/solve.py "$TMP/handout")"
echo "$OUT" | tail -8

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

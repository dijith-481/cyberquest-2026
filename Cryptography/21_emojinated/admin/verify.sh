#!/usr/bin/env bash
# Emojinated — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, solves a fresh copy, checks flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{3m0t1c0ns_w4llb04rd_b7ae2865}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/make_wallboard.py >/dev/null
cp -r handout "$TMP/handout"

OUT="$(python3 admin/solve.py "$TMP/handout")"
echo "$OUT" | tail -n 3

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

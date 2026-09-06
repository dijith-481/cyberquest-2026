#!/usr/bin/env bash
# the_corridor_that_remembers — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, runs the reference solve
# against a fresh copy, and checks the recovered flag.
# Requires: python3, gcc, strip.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{familiar_is_not_the_same_as_correct}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/make_handout.py >/dev/null
cp handout/corridor.tar.gz "$TMP/corridor.tar.gz"

OUT="$(python3 admin/solve.py "$TMP/corridor.tar.gz")"
echo "$OUT"

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

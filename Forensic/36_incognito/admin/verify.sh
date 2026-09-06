#!/usr/bin/env bash
# incognito — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, runs the reference solve
# against a fresh copy, and checks the recovered flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{1nc0gn1t0_l34v3s_th3_w4l_b3h1nd_9f4c2e}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/make_handout.py >/dev/null
cp -r handout "$TMP/handout"

OUT="$(python3 admin/solve.py "$TMP/handout")"
echo "$OUT"

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

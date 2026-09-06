#!/usr/bin/env bash
# clock_skew — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, breaks a fresh copy, checks flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{t0tp_4nd_th3_c10ck_th4t_l13d_7f30aa}'

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

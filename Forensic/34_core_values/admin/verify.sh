#!/usr/bin/env bash
# core_values — verify the challenge is solvable end to end.
# Recompiles the culture app, regenerates the heap dump, runs the
# reference solve against a fresh copy, and checks the recovered flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{v4lu3s_4rr1v3_0ut_0f_0rd3r_k33p_th3_s3q_b3f19}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/make_handout.py >/dev/null
cp handout/valuesd_heap.raw "$TMP/"

OUT="$(python3 admin/solve.py "$TMP/valuesd_heap.raw")"
echo "$OUT"

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

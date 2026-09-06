#!/usr/bin/env bash
# complexity_requirements — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, cracks a fresh copy, checks flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{c0mpli4nt_bu7_pr3dict4bl3_5e8817}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/make_export.py >/dev/null
cp -r handout "$TMP/handout"

OUT="$(python3 admin/solve.py "$TMP/handout")"
echo "$OUT"

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

#!/usr/bin/env bash
# unsaved_changes — verify the challenge is solvable end to end.
# Regenerates the handout deterministically (real vim), then runs the
# reference solve against a fresh copy.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{uns4ved_n0t3s_r3m3mb3r_3v3ryth1ng_5a91c4}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/make_handout.py >/dev/null
cp -r handout "$TMP/handout"
rm -f "$TMP/handout/.gitkeep" 2>/dev/null || true

OUT="$(python3 admin/solve.py "$TMP/handout")"
echo "$OUT"

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

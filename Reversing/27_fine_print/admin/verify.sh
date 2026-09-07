#!/usr/bin/env bash
# fine_print — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, runs the reference solve
# against a fresh copy, and checks the recovered flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{x0r_a11_th3_str1ngs_2gether_3f8a1d}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/generate.py --seed oe-fine-print-27 >/dev/null
cp -r handout "$TMP/handout"
rm -f "$TMP/handout/.gitkeep" 2>/dev/null || true

OUT="$(python3 admin/solve.py "$TMP/handout")"
echo "$OUT"

# The runtime must never leak the flag on its own.
if "$TMP/handout/licenseguard" anything 2>/dev/null | grep -q "$EXPECTED"; then
  echo "VERIFY FAILED — binary leaks flag at runtime" >&2
  exit 1
fi

# The tell must be exactly four strings at flag length.
TELL="$(strings "$TMP/handout/licenseguard" | awk -v n="${#EXPECTED}" 'length == n' | wc -l)"
if [ "$TELL" -ne 4 ]; then
  echo "VERIFY FAILED — expected 4 tell strings, found $TELL" >&2
  exit 1
fi

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

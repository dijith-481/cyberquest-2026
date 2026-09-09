#!/usr/bin/env bash
# uglified — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, runs the reference solve
# against a fresh copy, and checks the recovered flag with the bundle.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{m1n1f13d_n0t_h1dd3n_5d7e1a}'
FAKE='cyber_quest{fr33_w4rr4nty_cl41m_4ppr0v3d}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/generate.py --seed oe-uglified-30 >/dev/null
cp -r handout "$TMP/handout"

OUT="$(python3 admin/solve.py "$TMP/handout")"
echo "$OUT"

# The bundle must accept the recovered flag and reject junk + empty input.
ACCEPT="$(node "$TMP/handout/bundle.js" "$OUT")"
echo "$ACCEPT"
if node "$TMP/handout/bundle.js" "nope" >/dev/null 2>&1; then
  echo "VERIFY FAILED — bundle accepts junk" >&2
  exit 1
fi
if node "$TMP/handout/bundle.js" >/dev/null 2>&1; then
  echo "VERIFY FAILED — bundle accepts empty input" >&2
  exit 1
fi

# The real flag must never appear in the handout; the decoy must.
if grep -rqF "$EXPECTED" "$TMP/handout"; then
  echo "VERIFY FAILED — handout leaks the real flag" >&2
  exit 1
fi
if ! grep -rqF "$FAKE" "$TMP/handout"; then
  echo "VERIFY FAILED — decoy receipt missing from handout" >&2
  exit 1
fi

if [ "$OUT" = "$EXPECTED" ]; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

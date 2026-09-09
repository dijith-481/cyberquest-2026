#!/usr/bin/env bash
# invisible_ink — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, runs the reference solve
# against a fresh copy, executes the extracted payload under node,
# and checks the recovered flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{wh1t3sp4c3_supply_ch41n_8f3a2c}'
DECOY='cyber_quest{d3pr3c4t3d_v1_s3al_r3m0v3d}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/generate.py --seed oe-invisible-ink-29 >/dev/null
cp -r handout "$TMP/handout"

OUT="$(python3 admin/solve.py "$TMP/handout")"
echo "$OUT"

# The visible module must stay valid JS.
node --check "$TMP/handout/index.js"

# The extracted payload must be valid JS that prints the flag under node.
python3 admin/solve.py --emit-payload "$TMP/handout" > "$TMP/seal.js"
node --check "$TMP/seal.js"
{ cat "$TMP/seal.js"; echo 'console.log(unseal());'; } > "$TMP/run.js"
OUT2="$(node "$TMP/run.js")"
echo "$OUT2"

# Trailing whitespace must actually be present (the whole point).
if ! grep -rPn ' $|\t$' "$TMP/handout/index.js" >/dev/null; then
  echo "VERIFY FAILED — no trailing whitespace in index.js" >&2
  exit 1
fi

# The real flag must never appear in the handout; the decoy must.
if grep -rqF "$EXPECTED" "$TMP/handout"; then
  echo "VERIFY FAILED — handout leaks the real flag" >&2
  exit 1
fi
if ! grep -rqF "$DECOY" "$TMP/handout"; then
  echo "VERIFY FAILED — decoy flag missing from handout" >&2
  exit 1
fi

if [ "$OUT" = "$EXPECTED" ] && [ "$OUT2" = "$EXPECTED" ]; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

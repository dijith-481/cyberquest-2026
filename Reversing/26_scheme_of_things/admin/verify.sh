#!/usr/bin/env bash
# scheme_of_things — verify the challenge is solvable end to end.
# Regenerates the binary deterministically from the seed, confirms the
# committed handout is byte-identical, recovers the statement with the
# reference DFS solver, and asserts the flag (plus negative tests).
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{ch41n3d_b4cktr4ck1ng_9d41f3}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/generate.py --out "$TMP/build" >/dev/null

# The committed handout must be byte-identical to a fresh regeneration.
if ! cmp -s handout/evaluator "$TMP/build/player/evaluator"; then
  echo "VERIFY FAILED — handout/evaluator differs from a fresh regeneration" >&2
  exit 1
fi

PASS="$(python3 "$TMP/build/organizer/solve_reference.py" "$TMP/build/organizer/metadata.json")"
OUT="$(printf '%s\n' "$PASS" | "$TMP/build/player/evaluator")"
echo "$OUT"

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — statement recovered by backtracking DFS, flag revealed"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

# Negative controls: grammar violations and near-miss values must be rejected.
for BAD in 'chain the state and backtrack 26' '(chain the state' '(chain the state and backtrack 27)'; do
  if printf '%s\n' "$BAD" | "$TMP/build/player/evaluator" | grep -q "$EXPECTED"; then
    echo "VERIFY FAILED — accepted: $BAD" >&2
    exit 1
  fi
done
echo "VERIFY OK — negative controls rejected"

#!/usr/bin/env bash
# scheme_of_things — verify the challenge is solvable end to end.
# Regenerates the binary deterministically from the seed, recovers the
# passphrase with the reference solver, and asserts the flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{struktur3_n0t_str1ngs_9c4e7a}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/generate.py --out "$TMP/build" >/dev/null

PASS="$(python3 "$TMP/build/organizer/solve_reference.py" "$TMP/build/organizer/metadata.json")"
OUT="$(printf '%s\n' "$PASS" | "$TMP/build/player/evaluator")"
echo "$OUT"

# The committed handout must be byte-identical to a fresh regeneration.
if ! cmp -s handout/evaluator "$TMP/build/player/evaluator"; then
  echo "VERIFY FAILED — handout/evaluator differs from a fresh regeneration" >&2
  exit 1
fi

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — passphrase recovered, flag revealed from a fresh binary"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

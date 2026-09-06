#!/usr/bin/env bash
# ghost_glyphs — verify the challenge is solvable end to end.
# Regenerates the handout from the seed, checks the SVG leaks nothing,
# and runs the static reference solver against the shipped file.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{0nly_th3_r1ght_0bserver_s33s_th3_s1gn4l_9d4e2f}'
SEED=43
DECOY='cyber_quest{n0_s1gn4l_d3t3ct3d}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. the generator must reproduce the handout byte-for-byte
python3 deployment/generate.py --seed "$SEED" --flag "$EXPECTED" --out "$TMP/regen.svg" >/dev/null
cmp handout/archive_07.svg "$TMP/regen.svg"

# 2. well-formed XML (handout as shipped)
python3 -c 'import sys, xml.dom.minidom; xml.dom.minidom.parse("handout/archive_07.svg")'
echo "XML well-formed"

# 3. the real flag must never appear as text anywhere in the file
if grep -qF "$EXPECTED" handout/archive_07.svg; then
  echo "VERIFY FAILED — real flag leaks in plaintext" >&2
  exit 1
fi
echo "no plaintext flag leak"

# 4. decoy flag-shaped text must be present (the grep trap)
grep -qF "$DECOY" handout/archive_07.svg
echo "decoy flag present"

# 5. SVG2 <use href> indirection, and no legacy xlink
grep -q '<use href="#' handout/archive_07.svg
if grep -q 'xlink:href' handout/archive_07.svg; then
  echo "VERIFY FAILED — legacy xlink:href found" >&2
  exit 1
fi

# 6. embedded inner SVG (calibration plate) present
grep -q 'data:image/svg+xml;base64' handout/archive_07.svg
echo "calibration plate present"

# 7. reference solve: recover the flag statically from the shipped file
OUT="$(python3 admin/solve.py handout/archive_07.svg | tail -n 1)"
echo "recovered: $OUT"
if [ "$OUT" != "$EXPECTED" ]; then
  echo "VERIFY FAILED — solver recovered $OUT" >&2
  exit 1
fi

echo "VERIFY OK — handout encodes the flag, leaks nothing, and solves statically"

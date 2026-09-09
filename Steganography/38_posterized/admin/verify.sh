#!/usr/bin/env bash
# 38_posterized — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, checks PNG structure,
# runs the reference solve against a fresh copy, checks the flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{p41r_0rd3r_8f2a}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/generate.py >/dev/null
cp handout/launch-poster.png "$TMP/launch-poster.png"

python3 - <<'EOF' "$TMP/launch-poster.png"
import struct, sys, zlib
d = open(sys.argv[1], "rb").read()
assert d[:8] == b"\x89PNG\r\n\x1a\n", "bad signature"
pos, types, ctype, plen = 8, [], None, 0
while pos < len(d):
    ln = struct.unpack(">I", d[pos:pos+4])[0]
    typ, data = d[pos+4:pos+8], d[pos+8:pos+8+ln]
    assert zlib.crc32(d[pos+4:pos+8+ln]) & 0xffffffff == struct.unpack(">I", d[pos+8+ln:pos+12+ln])[0], f"bad CRC in {typ}"
    types.append(typ.decode())
    if typ == b"IHDR":
        ctype = struct.unpack(">IIBBBBB", data)[3]
    if typ == b"PLTE":
        plen = len(data) // 3
    pos += 12 + ln
assert types == ["IHDR", "PLTE", "IDAT", "IEND"], f"unexpected chunks: {types}"
assert ctype == 3, f"not indexed color: {ctype}"
assert plen == 256, f"PLTE has {plen} entries, want 256"
print(f"structure OK: {types}, indexed, 256-entry PLTE")
EOF

OUT="$(python3 admin/solve.py "$TMP/launch-poster.png")"
echo "$OUT"

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

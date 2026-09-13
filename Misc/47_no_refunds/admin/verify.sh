#!/usr/bin/env bash
# No Refunds — verify the challenge end to end (stdlib only).
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{sc4n_th3_r3ce1pt_47c1d4}'
SEED=47
FILE='handout/receipt.png'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. generator must reproduce the handout byte-for-byte
python3 deployment/generate.py --seed "$SEED" --flag "$EXPECTED" --out "$TMP/regen.png" >/dev/null
cmp "$FILE" "$TMP/regen.png"
echo "handout reproducible from seed $SEED"

# 2. PNG sanity: signature, dimensions, no text chunks
python3 - <<'EOF'
import struct, zlib
from pathlib import Path
d = Path("handout/receipt.png").read_bytes()
assert d[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
off, seen = 8, set()
while off < len(d):
    (ln,) = struct.unpack(">I", d[off:off+4])
    typ = d[off+4:off+8]
    seen.add(typ)
    if typ == b"IHDR":
        w, h, bitd, ctyp, _, _, _ = struct.unpack(">IIBBBBB", d[off+8:off+8+ln])
        assert (w, h) == (960, 1400), (w, h)
        assert bitd == 8 and ctyp == 2
    off += 12 + ln
assert b"IEND" in seen
assert not (seen & {b"tEXt", b"zTXt", b"iTXt"}), "text chunk leaks metadata"
print("PNG 960x1400 truecolor, no text chunks")
EOF

# 3. flag must not appear as bytes anywhere in the handout
if grep -qF "$EXPECTED" "$FILE"; then
  echo "VERIFY FAILED — flag leaks in PNG bytes" >&2
  exit 1
fi
echo "no plaintext flag leak"

# 4. reference solve recovers the flag
OUT="$(python3 admin/solve.py "$FILE" | tail -n 1)"
echo "recovered: $OUT"
if [ "$OUT" != "$EXPECTED" ]; then
  echo "VERIFY FAILED — solver recovered $OUT" >&2
  exit 1
fi

echo "VERIFY OK — upside-down receipt rotates and scans to the flag"

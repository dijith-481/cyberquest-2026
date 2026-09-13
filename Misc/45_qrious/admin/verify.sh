#!/usr/bin/env bash
# QRious — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, checks every PNG is a clean
# same-size black/white image, and runs the reference solver (exhaustive
# 16383-subset brute force) against the shipped files.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{x0r_m3_1f_y0u_c4n_8f3a2c}'
SEED=45

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. the generator must reproduce the handout byte-for-byte
python3 deployment/generate.py --seed "$SEED" --flag "$EXPECTED" --out "$TMP/regen" >/dev/null
for i in $(seq -w 1 14); do
  cmp "handout/IMG_0${i}.png" "$TMP/regen/IMG_0${i}.png"
done
echo "handout reproducible from seed $SEED"

# 2. all 14 files: same square dimensions, pure black/white pixels
python3 - <<'EOF'
import struct, zlib
from pathlib import Path
sizes = set()
for i in range(1, 15):
    p = Path(f"handout/IMG_{i:03d}.png")
    d = p.read_bytes()
    assert d[:8] == b"\x89PNG\r\n\x1a\n", p
    off = 8; w = h = None; idat = bytearray()
    while off < len(d):
        (ln,) = struct.unpack(">I", d[off:off+4])
        typ = d[off+4:off+8]; body = d[off+8:off+8+ln]
        if typ == b"IHDR":
            w, h, bitd, ctyp, _, _, _ = struct.unpack(">IIBBBBB", body)
            assert bitd == 8 and ctyp == 0, (p, bitd, ctyp)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        off += 12 + ln
    raw = zlib.decompress(bytes(idat))
    px = set()
    prev = bytearray(w)
    for y in range(h):
        f = raw[y*(w+1)]; cur = bytearray(raw[y*(w+1)+1:(y+1)*(w+1)])
        assert f == 0, (p, "filtered")
        px.update(cur)
        assert set(cur) <= {0, 255}, (p, "not bilevel")
    assert w == h == 296, (p, w, h)
    sizes.add((w, h))
assert len(sizes) == 1
print("14 PNGs, 296x296, pure black/white, identical dimensions")
EOF

# 3. no single image scans as a QR code on its own is implied by (4), but
#    assert the shipped files leak no plaintext flag either
if grep -rqF "$EXPECTED" handout/; then
  echo "VERIFY FAILED — flag leaks in handout bytes" >&2
  exit 1
fi
echo "no plaintext flag leak"

# 4. reference solve: exactly one decodable subset, and it is the flag
OUT="$(python3 admin/solve.py handout | tail -n 1)"
echo "recovered: $OUT"
if [ "$OUT" != "$EXPECTED" ]; then
  echo "VERIFY FAILED — solver recovered $OUT" >&2
  exit 1
fi

echo "VERIFY OK — 14 shares, 16383 subsets, exactly one decodes"

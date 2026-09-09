#!/usr/bin/env bash
# 41_tracking — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, checks TTF structure,
# confirms the decoy channels carry nothing, confirms file-order parity
# does NOT decode (the proof list is load-bearing), runs the reference solve.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{k3rn1ng_0n3_un1t_m4tt3rs_c41f}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/generate.py >/dev/null
cp handout/brand-display.ttf "$TMP/regen.ttf"
cp handout/specimen.html "$TMP/specimen.html"
cmp handout/brand-display.ttf "$TMP/regen.ttf"
cmp handout/specimen.html "$TMP/specimen.html"
echo "handout reproducible"

python3 - <<'EOF'
import struct
d = open("handout/brand-display.ttf", "rb").read()
assert struct.unpack(">I", d[:4])[0] == 0x00010000, "bad sfnt version"
n = struct.unpack(">H", d[4:6])[0]
tabs = {}
for i in range(n):
    tag, chk, off, ln = struct.unpack(">4sIII", d[12+i*16:28+i*16])
    body = bytearray(d[off:off+ln])
    if tag == b"head":
        body[8:12] = b"\0\0\0\0"  # adjustment is defined to checksum as zero
    pad = bytes(body) + b"\0" * ((-ln) % 4)
    calc = sum(struct.unpack(">%dI" % (len(pad)//4), pad)) & 0xFFFFFFFF
    assert calc == chk, f"bad checksum in {tag}"
    tabs[tag.decode()] = (off, ln)
for t in ("cmap", "glyf", "head", "hhea", "hmtx", "loca", "maxp",
          "name", "OS/2", "post", "GPOS"):
    assert t in tabs, f"missing table {t}"
print("sfnt ok: 11 tables, checksums valid")
total = sum(struct.unpack(">%dI" % (len(d)//4), d)) & 0xFFFFFFFF
assert total == 0xB1B0AFBA, f"bad checkSumAdjustment: {total:08x}"
print("checkSumAdjustment ok")
EOF

python3 - <<'EOF'
import re, struct, sys
sys.path.insert(0, "admin")
from solve import tables, kern_dict, cmap_gids
d = open("handout/brand-display.ttf", "rb").read()
tabs = tables(d)
kern = kern_dict(tabs[b"GPOS"])
assert len(kern) == 676, f"want all 676 cap pairs, have {len(kern)}"
print("676 kern pairs present (message + decoys)")

# single-channel property: advances constant, flag never in plaintext
moff = None
n = struct.unpack(">H", d[4:6])[0]
for i in range(n):
    if d[12+i*16:16+i*16] == b"maxp":
        moff = struct.unpack(">I", d[16+i*16+4:16+i*16+8])[0]
    if d[12+i*16:16+i*16] == b"hmtx":
        hoff = struct.unpack(">I", d[16+i*16+4:16+i*16+8])[0]
ng = struct.unpack(">H", d[moff+4:moff+6])[0]
adv = [struct.unpack(">H", d[hoff+4*i:hoff+4*i+2])[0] for i in range(ng)]
assert set(adv) <= {300, 600} and adv.count(300) == 1
print(f"hmtx constant ({ng} glyphs): decoy channel empty")
assert b"cyber_quest" not in d, "flag leaks in plaintext"

# the proof list is load-bearing: file-order parity must NOT decode
g = tabs[b"GPOS"]
_ver, _s, _f, l = struct.unpack(">IHHH", g[:10])
loff = l + struct.unpack(">H", g[l+2:l+4])[0]
base = loff + struct.unpack(">H", g[loff+6:loff+8])[0]
npair = struct.unpack(">H", g[base+8:base+10])[0]
bits = []
for r in range(npair):
    ps = base + struct.unpack(">H", g[base+10+2*r:base+12+2*r])[0]
    for k in range(struct.unpack(">H", g[ps:ps+2])[0]):
        bits.append(struct.unpack(">h", g[ps+4+4*k:ps+6+4*k])[0] & 1)
raw = bytes(int("".join(map(str, bits[i:i+8])), 2)
            for i in range(0, len(bits)-len(bits)%8, 8))
assert raw[:2] != b"CQ", "file-order parity still decodes: too easy"
print("file-order parity is garbage: proof order required")

html = open("handout/specimen.html", encoding="utf-8").read()
m = re.search(r'<pre[^>]*id="kern-proof"[^>]*>(.*?)</pre>', html, re.S)
toks = [t for t in re.split(r"\s+", m.group(1))
        if len(t) == 2 and t.isalpha() and t.isupper()]
assert len(toks) == 400, f"proof lists {len(toks)} pairs, want 400"
gids = cmap_gids(tabs[b"cmap"])
assert all(t[0] in gids and t[1] in gids for t in toks)
assert all((gids[t[0]], gids[t[1]]) in kern for t in toks)
print("proof lists 400 pairs, all present in GPOS")
EOF

OUT="$(python3 admin/solve.py handout/brand-display.ttf handout/specimen.html)"
echo "$OUT"
if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi

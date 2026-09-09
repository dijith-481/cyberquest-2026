#!/usr/bin/env python3
"""41_tracking — generate handout/brand-display.ttf + handout/specimen.html.

A minimal but valid TrueType display face ("Brand Display", stdlib only,
deterministic, seed 41) with a systematic GPOS kerning table.

Encoding (one elegant mechanism, nothing else):
  GPOS PairPos Format 1 holds uppercase pairs in alphabetical order:
      AA AB AC ... AZ BA BB ... (row-major over A-Z)
  Each kerning XAdvance is a plausible negative tightening value whose
  PARITY carries one bit:
      even value -> 0
      odd value  -> 1        (one font unit off — invisible)
  File order of the PairSet records IS the bit order, MSB first.

Bitstream framing (same envelope as the other media challenges, so a
correct extraction confirms itself):
  magic   2 bytes  "CQ" (0x43 0x51)
  length  u16 BE   len(payload)
  payload bytes    the full flag, ASCII
  crc32   u32 BE   zlib CRC32 of payload

Anti-channels: every advance width is identical (600, space 300) and every
glyph outline is a plain bar, so hmtx/cmap/glyf carry nothing.

Glyph set: .notdef + U+0020, U+002D..U+002E, U+0030..U+0039, U+0041..U+005A,
U+005F, U+0061..U+007D (70 glyphs). All outlines are single-contour
rectangles of per-glyph width; advances are constant.
"""
import datetime
import os
import random
import struct
import zlib

SEED = 41
FLAG = "cyber_quest{k3rn1ng_0n3_un1t_m4tt3rs_c41f}"
UPM = 1000

# codepoints after .notdef, in order (gid 1..69)
CODEPOINTS = (
    [0x20, 0x2D, 0x2E]
    + list(range(0x30, 0x3A))
    + list(range(0x41, 0x5B))
    + [0x5F]
    + list(range(0x61, 0x7E))
)
assert len(CODEPOINTS) == 69
NUM_GLYPHS = 70

# standard Mac glyph-order indices for the post table (all < 258)
STD_INDEX = {0x20: 3, 0x2D: 16, 0x2E: 17, 0x5F: 66, 0x7B: 94, 0x7C: 95, 0x7D: 96}
for d in range(10):
    STD_INDEX[0x30 + d] = 19 + d
for i in range(26):
    STD_INDEX[0x41 + i] = 36 + i
    STD_INDEX[0x61 + i] = 68 + i

EVEN_BASES = [-84, -80, -76, -72, -68, -64, -60]  # plausible tightenings


def frame_payload(flag: str) -> bytes:
    payload = flag.encode("ascii")
    return b"CQ" + struct.pack(">H", len(payload)) + payload + struct.pack(
        ">I", zlib.crc32(payload) & 0xFFFFFFFF
    )


def mac_epoch_seconds(year, month, day):
    base = datetime.datetime(1904, 1, 1)
    dt = datetime.datetime(year, month, day)
    return int((dt - base).total_seconds())


def glyph_data(cp):
    """(glyf bytes, advance, lsb, xMax). Empty for .notdef/space."""
    if cp is None or cp == 0x20:
        return struct.pack(">hhhhh", 0, 0, 0, 0, 0), 600 if cp is None else 300, 0, 0
    w = 300 + (cp * 53) % 250
    x0, y0, x1, y1 = 50, 0, 50 + w, 700
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    xd = [pts[0][0]] + [pts[i][0] - pts[i - 1][0] for i in range(1, 4)]
    yd = [pts[0][1]] + [pts[i][1] - pts[i - 1][1] for i in range(1, 4)]
    rec = struct.pack(">hhhhh", 1, x0, y0, x1, y1)
    rec += struct.pack(">H", 3)          # endPts[0]
    rec += struct.pack(">H", 0)          # no instructions
    rec += bytes([0x01] * 4)             # all points on-curve
    rec += struct.pack(">4h", *xd)
    rec += struct.pack(">4h", *yd)
    assert len(rec) % 2 == 0
    return rec, 600, 50, x1


def build_gpos(bits):
    """Return (GPOS bytes, message pairs in bit order).

    The 400 message pairs live alphabetically (AA..AZ, BA..BZ, ... PA..PJ)
    but are stored in SEEDED-SHUFFLED file order, mixed with the remaining
    276 uppercase pairs as random-parity decoys (same value distribution,
    so values alone do not distinguish). Total: all 676 A-Z pairs.
    Bit order comes ONLY from the specimen's tracking-proof list.
    """
    rng = random.Random(SEED)
    msg_pairs = [(a, b) for a in range(26) for b in range(26)][: len(bits)]
    assert len(msg_pairs) == len(bits), "need <= 676 bits"
    gid_of = {chr(0x41 + i): 14 + i for i in range(26)}  # gid 14..39 = A..Z

    values = {}  # (first, second) -> XAdvance
    for (a, b), bit in zip(msg_pairs, bits):
        first, second = chr(0x41 + a), chr(0x41 + b)
        base = rng.choice(EVEN_BASES)
        val = base if bit == 0 else base - 1
        assert (val & 1) == bit
        values[(first, second)] = val
    msg_set = set(msg_pairs)
    for a in range(26):
        for b in range(26):
            if (a, b) not in msg_set:
                first, second = chr(0x41 + a), chr(0x41 + b)
                values[(first, second)] = rng.choice(EVEN_BASES) - rng.getrandbits(1)

    # storage order: fully shuffled
    firsts = [chr(0x41 + i) for i in range(26)]
    rng.shuffle(firsts)
    rows = {}
    for f in firsts:
        recs = [(gid_of[s], values[(f, s)]) for s in
                [chr(0x41 + i) for i in range(26)]]
        rng.shuffle(recs)
        rows[f] = recs

    msg_order = [(chr(0x41 + a), chr(0x41 + b)) for a, b in msg_pairs]

    coverage = struct.pack(">HH", 1, len(firsts))
    for f in firsts:
        coverage += struct.pack(">H", gid_of[f])

    pairsets = b""
    pair_offsets = []
    for f in firsts:
        recs = rows[f]
        pair_offsets.append(len(pairsets))
        pairsets += struct.pack(">H", len(recs))
        for second, val in recs:
            pairsets += struct.pack(">Hh", second, val)

    n = len(firsts)
    pairpos = struct.pack(">HHHHH", 1, 0, 4, 0, n)  # fmt,covOff,vf1,vf2,count
    cov_off = 10 + 2 * n
    pairpos = struct.pack(">HHHHH", 1, cov_off, 4, 0, n)
    for i in range(n):
        pairpos += struct.pack(">H", cov_off + len(coverage) + pair_offsets[i])
    pairpos += coverage + pairsets

    lookup = struct.pack(">HHHH", 2, 0, 1, 8) + pairpos  # type2,flag,1,off
    lookup_list = struct.pack(">H", 1) + struct.pack(">H", 4) + lookup
    feature = struct.pack(">HHH", 0, 1, 0)  # params NULL, 1 lookup, lookup 0
    feature_list = struct.pack(">H", 1) + b"kern" + struct.pack(">H", 8) + feature
    langsys = struct.pack(">HHH", 0, 0xFFFF, 1) + struct.pack(">H", 0)
    script = struct.pack(">HH", 4, 0) + langsys  # defaultLangSys + langSysCount
    script_list = struct.pack(">H", 1) + b"DFLT" + struct.pack(">H", 8) + script

    gpos = struct.pack(">IHHH", 0x00010000, 16, 0, 0)  # ver, script, feat, look
    s_off = 10
    f_off = s_off + len(script_list)
    l_off = f_off + len(feature_list)
    gpos = struct.pack(">IHHH", 0x00010000, s_off, f_off, l_off)
    gpos += script_list + feature_list + lookup_list
    return gpos, msg_order


def table_checksum(data):
    padded = data + b"\0" * ((-len(data)) % 4)
    return sum(struct.unpack(">%dI" % (len(padded) // 4), padded)) & 0xFFFFFFFF


SPECIMEN = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Brand Display — type specimen</title>
<style>
  @font-face {
    font-family: 'Brand Display';
    src: url('brand-display.ttf') format('truetype');
  }
  body { font-family: 'Brand Display', sans-serif; max-width: 640px;
         margin: 40px auto; padding: 0 24px; color: #1a1a1a; }
  .meta { font-size: 13px; opacity: 0.65; }
  h1 { font-size: 44px; margin: 8px 0; }
  .alpha { font-size: 26px; line-height: 1.6; }
  .note { font-size: 15px; border-left: 3px solid #1a1a1a;
           padding-left: 12px; margin-top: 28px; }
  .proof { font-size: 15px; line-height: 1.9; }
</style>
</head>
<body>
<p class="meta">Ordinary Engineering &mdash; internal type specimen v1.0 (unreleased)</p>
<h1>Brand Display</h1>
<p class="alpha">ABCDEFGHIJKLMNOPQRSTUVWXYZ</p>
<p class="alpha">abcdefghijklmnopqrstuvwxyz</p>
<p class="alpha">0123456789 - . _{}|</p>
<div class="note">
<p>Tracking is precise. Even one unit matters.</p>
<p class="meta">Display cut, 1000 upm. Tighten cap pairs before release.</p>
</div>
<h2>Tracking proof</h2>
<p class="meta">Cap pairs, set in reading order. Proof order is binding.</p>
<pre class="proof" id="kern-proof">
__PROOF__
</pre>
</body>
</html>
"""


def main():
    rng = random.Random(SEED)
    packet = frame_payload(FLAG)
    bits = [(b >> (7 - i)) & 1 for b in packet for i in range(8)]
    print(f"flag: {FLAG}")
    print(f"packet: {len(packet)} bytes -> {len(bits)} bits")

    # ---- glyphs ----
    records, advances, xmax = [], [], 0
    empty, adv0, lsb0, _ = glyph_data(None)
    records.append(empty)
    advances.append((adv0, lsb0))
    for cp in CODEPOINTS:
        rec, adv, lsb, x = glyph_data(cp)
        records.append(rec)
        advances.append((adv, lsb))
        xmax = max(xmax, x)

    glyf = b"".join(records)
    loca_vals, off = [0], 0
    for rec in records:
        off += len(rec)
        loca_vals.append(off // 2)
    loca = struct.pack(">%dH" % len(loca_vals), *loca_vals)
    hmtx = b"".join(struct.pack(">Hh", a, l) for a, l in advances)

    # ---- cmap format 4 ----
    starts = [0x20, 0x2D, 0x30, 0x41, 0x5F, 0x61, 0xFFFF]
    ends = [0x20, 0x2E, 0x39, 0x5A, 0x5F, 0x7D, 0xFFFF]
    gid_start = [1, 2, 4, 14, 40, 41, 0]
    deltas = [(g - s) & 0xFFFF if s != 0xFFFF else 1 for g, s in zip(gid_start, starts)]
    seg = len(starts)
    cmap_sub = struct.pack(">HHHHHHH", 4, 16 + 8 * seg, 0, seg * 2, 8, 2, 2 * seg - 8)
    cmap_sub += struct.pack(">%dH" % seg, *ends)
    cmap_sub += struct.pack(">H", 0)
    cmap_sub += struct.pack(">%dH" % seg, *starts)
    cmap_sub += struct.pack(">%dH" % seg, *deltas)
    cmap_sub += struct.pack(">%dH" % seg, *([0] * seg))
    cmap = struct.pack(">HH", 0, 1) + struct.pack(">HHI", 3, 1, 12) + cmap_sub

    # ---- name ----
    strs = [
        (1, "Brand Display"), (2, "Regular"), (3, "Brand Display Regular 1.0"),
        (4, "Brand Display Regular"), (5, "Version 1.0"), (6, "BrandDisplay-Regular"),
    ]
    enc = [s.encode("utf-16-be") for _, s in strs]
    name = struct.pack(">HHH", 0, len(strs), 6 + 12 * len(strs))
    off = 0
    for (nid, _s), e in zip(strs, enc):
        name += struct.pack(">HHHHHH", 3, 1, 0x409, nid, len(e), off)
        off += len(e)
    for e in enc:
        name += e

    # ---- OS/2 v0 ----
    os2 = struct.pack(
        ">HHHHHhhhhhhhhhhh10sIIII4sHHHhhhHH",
        0, 600, 400, 5, 0,
        650, 700, 0, 140, 650, 700, 0, 480, 50, 300,
        0, b"\0" * 10,
        0x00000001, 0, 0, 0, b"OE  ",
        0x40, 0x20, 0x7D, 800, -200, 0, 800, 200,
    )

    # ---- head (adjustment patched later) ----
    created = mac_epoch_seconds(2026, 1, 12)
    head = struct.pack(
        ">IIIIHHQQhhhhHHhhh",
        0x00010000, 0x00010000, 0, 0x5F0F3CF5, 3, UPM,
        created, created + 3600, 0, 0, xmax, 700, 0, 8, 2, 0, 0,
    )

    # ---- hhea / maxp / post ----
    hhea = struct.pack(
        ">IhhhHhhhhhhhhhhhH",
        0x00010000, 800, -200, 0, 600, 0, 0, 600,
        1, 0, 0, 0, 0, 0, 0, 0, NUM_GLYPHS,
    )
    maxp = struct.pack(
        ">IH" + "H" * 13, 0x00010000, NUM_GLYPHS,
        4, 1, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1,
    )
    post = struct.pack(">IihhIIIII", 0x00020000, 0, -100, 50, 0, 0, 0, 0, 0)
    post += struct.pack(">H", NUM_GLYPHS)
    post += struct.pack(">%dH" % NUM_GLYPHS, 0, *[STD_INDEX[c] for c in CODEPOINTS])

    gpos, msg_order = build_gpos(bits)

    tables = {
        b"cmap": cmap, b"glyf": glyf, b"head": head, b"hhea": hhea,
        b"hmtx": hmtx, b"loca": loca, b"maxp": maxp, b"name": name,
        b"OS/2": os2, b"post": post, b"GPOS": gpos,
    }
    tags = sorted(tables)
    n = len(tags)
    sr = (2 ** (n.bit_length() - 1)) * 16
    header = struct.pack(">IHHHH", 0x00010000, n, sr, n.bit_length() - 1, n * 16 - sr)
    dirlen = 12 + 16 * n
    first = (dirlen + 3) & ~3
    offset = first
    recs, blob = b"", b""
    for tag in tags:
        data = tables[tag]
        padded = data + b"\0" * ((-len(data)) % 4)
        recs += struct.pack(">4sIII", tag, table_checksum(data), offset, len(data))
        blob += padded
        offset += len(padded)
    font = bytearray(header + recs)
    font += b"\0" * (first - len(font))
    font += blob
    total = sum(struct.unpack(">%dI" % (len(font) // 4), bytes(font))) & 0xFFFFFFFF
    adj = (0xB1B0AFBA - total) & 0xFFFFFFFF
    # head record is 3rd... find its file offset from recs
    for i, tag in enumerate(tags):
        if tag == b"head":
            hoff = struct.unpack(">I", recs[i * 16 + 8:i * 16 + 12])[0]
    font[hoff + 8:hoff + 12] = struct.pack(">I", adj)

    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "handout")
    os.makedirs(outdir, exist_ok=True)
    ttf = os.path.join(outdir, "brand-display.ttf")
    with open(ttf, "wb") as f:
        f.write(bytes(font))
    with open(os.path.join(outdir, "specimen.html"), "w") as f:
        rows = [" ".join(a + b for a, b in msg_order[i:i + 20])
                for i in range(0, len(msg_order), 20)]
        f.write(SPECIMEN.replace("__PROOF__", "\n".join(rows)))
    print(f"proof pairs: {len(msg_order)}")
    print(f"wrote {ttf} ({os.path.getsize(ttf)} bytes)")


if __name__ == "__main__":
    main()

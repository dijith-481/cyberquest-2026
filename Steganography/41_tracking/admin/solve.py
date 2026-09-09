#!/usr/bin/env python3
"""41_tracking — reference solver (stdlib only).

1. Read the tracking-proof order from specimen.html: the kern-proof block
   lists cap pairs "set in reading order" — that list IS the bit order.
2. Parse the font's cmap (format 4) to map A-Z to glyph IDs.
3. Parse GPOS PairPos (lookup type 2) subtables into a
   {(first, second): XAdvance} dict — file order is scrambled and mixed
   with decoy pairs, so direct indexing is required.
4. One bit per kerning XAdvance in proof order: value & 1, MSB first.
5. Parse the CQ framing: magic "CQ", u16-BE length, payload, u32-BE CRC32.
6. Verify the CRC and print the flag.
"""
import re
import struct
import sys
import zlib


def u16(b, o):
    return struct.unpack(">H", b[o:o + 2])[0]


def i16(b, o):
    return struct.unpack(">h", b[o:o + 2])[0]


def proof_order(path):
    html = open(path, encoding="utf-8").read()
    m = re.search(r'<pre[^>]*id="kern-proof"[^>]*>(.*?)</pre>', html, re.S)
    assert m, "no kern-proof block in specimen"
    toks = [t for t in re.split(r"\s+", m.group(1))
            if len(t) == 2 and t.isalpha() and t.isupper()]
    print(f"proof pairs: {len(toks)}", file=sys.stderr)
    return toks


def tables(data):
    assert struct.unpack(">I", data[:4])[0] == 0x00010000, "not a TTF sfnt"
    n = u16(data, 4)
    out = {}
    for i in range(n):
        tag, _chk, off, ln = struct.unpack(">4sIII", data[12 + i * 16:28 + i * 16])
        out[tag] = data[off:off + ln]
    return out


def cmap_gids(cmap):
    nc = u16(cmap, 2)
    sub = None
    for i in range(nc):
        plat, enc, off = struct.unpack(">HHI", cmap[4 + 8 * i:12 + 8 * i])
        if (plat, enc) == (3, 1):
            sub = cmap[off:]
            break
    assert sub and u16(sub, 0) == 4, "need a format-4 cmap"
    seg = u16(sub, 6) // 2
    ends = [u16(sub, 14 + 2 * i) for i in range(seg)]
    starts = [u16(sub, 16 + 2 * seg + 2 * i) for i in range(seg)]
    deltas = [u16(sub, 16 + 4 * seg + 2 * i) for i in range(seg)]
    ranges = [u16(sub, 16 + 6 * seg + 2 * i) for i in range(seg)]
    gids = {}
    for cp in range(0x41, 0x5B):
        for e, s, dl, ro, i in zip(ends, starts, deltas, ranges, range(seg)):
            if s <= cp <= e:
                assert ro == 0, "unexpected range-offset cmap"
                gids[chr(cp)] = (cp + dl) & 0xFFFF
                break
    assert len(gids) == 26, "A-Z must all be mapped"
    return gids


def kern_dict(gpos):
    _ver, _s, _f, l_off = struct.unpack(">IHHH", gpos[:10])
    out = {}
    for i in range(u16(gpos, l_off)):
        loff = l_off + u16(gpos, l_off + 2 + 2 * i)
        if u16(gpos, loff) != 2:
            continue
        for s in range(u16(gpos, loff + 4)):
            base = loff + u16(gpos, loff + 6 + 2 * s)
            assert u16(gpos, base) == 1, "want PairPos format 1"
            assert u16(gpos, base + 4) == 4, "want XAdvance-only values"
            cov = base + u16(gpos, base + 2)
            assert u16(gpos, cov) == 1, "want coverage format 1"
            npair = u16(gpos, base + 8)
            firsts = [u16(gpos, cov + 4 + 2 * i) for i in range(u16(gpos, cov + 2))]
            assert len(firsts) == npair
            for r in range(npair):
                ps = base + u16(gpos, base + 10 + 2 * r)
                for k in range(u16(gpos, ps)):
                    second = u16(gpos, ps + 2 + 4 * k)
                    out[(firsts[r], second)] = i16(gpos, ps + 4 + 4 * k)
    return out


def main(font_path, specimen_path):
    toks = proof_order(specimen_path)
    data = open(font_path, "rb").read()
    tabs = tables(data)
    gids = cmap_gids(tabs[b"cmap"])
    kern = kern_dict(tabs[b"GPOS"])
    print(f"kern pairs in font: {len(kern)}", file=sys.stderr)
    bits = []
    for t in toks:
        adv = kern[(gids[t[0]], gids[t[1]])]
        bits.append(adv & 1)
    assert len(bits) >= 48, "bitstream too short for a header"
    raw = bytes(
        int("".join(map(str, bits[k:k + 8])), 2)
        for k in range(0, len(bits) - len(bits) % 8, 8)
    )
    assert raw[:2] == b"CQ", f"bad magic: {raw[:2]!r}"
    (length,) = struct.unpack(">H", raw[2:4])
    payload = raw[4:4 + length]
    assert len(payload) == length, "bitstream truncated"
    (want,) = struct.unpack(">I", raw[4 + length:8 + length])
    got = zlib.crc32(payload) & 0xFFFFFFFF
    assert got == want, f"CRC mismatch: got {got:08x} want {want:08x}"
    print(f"crc ok ({got:08x}), payload {length} bytes", file=sys.stderr)
    print(payload.decode("ascii"))


if __name__ == "__main__":
    font = sys.argv[1] if len(sys.argv) > 1 else "brand-display.ttf"
    spec = sys.argv[2] if len(sys.argv) > 2 else "specimen.html"
    main(font, spec)

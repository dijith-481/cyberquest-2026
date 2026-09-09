#!/usr/bin/env python3
"""38_posterized — reference solver (stdlib only).

1. Parse the PNG, take the PLTE chunk (must be indexed color).
2. Pair entries that differ by exactly 1 in exactly one channel.
   Every entry must have exactly one such partner.
3. Bit per pair: smaller RGB value listed first -> 0, else 1.
4. Order pairs by ascending min(color value), concat bits MSB-first.
5. Bytes are the flag BODY (inner + "}"); prepend `cyber_quest{`.
"""
import struct
import sys
import zlib

def read_png(path):
    d = open(path, "rb").read()
    assert d[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, pal, ctype = 8, None, None
    while pos < len(d):
        ln = struct.unpack(">I", d[pos:pos + 4])[0]
        typ, data = d[pos + 4:pos + 8], d[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            ctype = struct.unpack(">IIBBBBB", data)[3]
        elif typ == b"PLTE":
            pal = [tuple(data[i:i + 3]) for i in range(0, len(data), 3)]
    assert ctype == 3, f"expected indexed color (type 3), got {ctype}"
    assert pal, "no PLTE chunk"
    return pal

def main(path):
    pal = read_png(path)
    n = len(pal)
    print(f"PLTE entries: {n}", file=sys.stderr)

    def is_pair(a, b):
        d = [abs(a[c] - b[c]) for c in range(3)]
        return sum(1 for v in d if v) == 1 and sum(d) == 1

    partner = {}
    for i in range(n):
        hits = [j for j in range(n) if j != i and is_pair(pal[i], pal[j])]
        assert len(hits) == 1, f"entry {i} {pal[i]}: {len(hits)} partners"
        partner[i] = hits[0]

    val = lambda c: (c[0] << 16) | (c[1] << 8) | c[2]
    seen, bits = set(), []
    pairs = []
    for i in range(n):
        if i in seen:
            continue
        j = partner[i]
        assert j not in seen and partner[j] == i
        seen.add(i)
        seen.add(j)
        pairs.append((i, j))
    pairs.sort(key=lambda pr: min(val(pal[pr[0]]), val(pal[pr[1]])))
    print(f"pairs: {len(pairs)}", file=sys.stderr)

    for i, j in pairs:
        # bit = 0 iff the smaller value sits at the smaller palette index
        a, b = (pal[i], pal[j])
        bit = 0 if (val(a) < val(b)) == (i < j) else 1
        bits.append(bit)

    assert len(bits) % 8 == 0
    body = bytes(
        int("".join(map(str, bits[k:k + 8])), 2)
        for k in range(0, len(bits), 8)
    )
    print(f"body bytes: {body!r}", file=sys.stderr)
    flag = "cyber_quest{" + body.decode()
    print(flag)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "launch-poster.png")

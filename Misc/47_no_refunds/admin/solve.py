#!/usr/bin/env python3
"""No Refunds — reference solver (stdlib only).

1. Read receipt.png, rotate 180 degrees back to upright.
2. Auto-locate the barcode band (tallest run of dark-heavy rows).
3. Run-length decode one scanline: Start B -> data -> checksum check
   -> stop, using the same Code 128-B table as the generator.

Usage:  python3 admin/solve.py handout/receipt.png
"""

import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "deployment"))
from generate import CHARSET_B, CODES, START_B, STOP_FULL  # noqa: E402


def read_png_rgb(path: str):
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    off = 8
    w = h = None
    idat = bytearray()
    while off < len(data):
        (ln,) = struct.unpack(">I", data[off:off + 4])
        typ = data[off + 4:off + 8]
        body = data[off + 8:off + 8 + ln]
        if typ == b"IHDR":
            w, h, bitd, ctyp, _, _, _ = struct.unpack(">IIBBBBB", body)
            assert bitd == 8 and ctyp == 2
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        off += 12 + ln
    raw = zlib.decompress(bytes(idat))
    px = bytearray(w * h * 3)
    for y in range(h):
        assert raw[y * (w * 3 + 1)] == 0
        px[y * w * 3:(y + 1) * w * 3] = raw[y * (w * 3 + 1) + 1:(y + 1) * (w * 3 + 1)]
    return px, w, h


def rotate180(px, w, h):
    out = bytearray(len(px))
    for y in range(h):
        for x in range(w):
            s = ((h - 1 - y) * w + (w - 1 - x)) * 3
            d = (y * w + x) * 3
            out[d:d + 3] = px[s:s + 3]
    return out


def lum(px, w, x, y):
    o = (y * w + x) * 3
    return (px[o] + px[o + 1] + px[o + 2]) // 3


def find_band(px, w, h):
    bands = []
    in_band = False
    start = 0
    for y in range(h):
        dark = sum(1 for x in range(w) if lum(px, w, x, y) < 128)
        if dark > w * 0.25 and not in_band:
            in_band, start = True, y
        elif dark <= w * 0.25 and in_band:
            in_band = False
            bands.append((start, y))
    if in_band:
        bands.append((start, h))
    assert bands, "no barcode band found"
    return max(bands, key=lambda b: b[1] - b[0])


def decode_row(px, w, y):
    runs = []
    cur, prev = 1, lum(px, w, 0, y) < 128
    for x in range(1, w):
        v = lum(px, w, x, y) < 128
        if v == prev:
            cur += 1
        else:
            runs.append((prev, cur))
            prev, cur = v, 1
    runs.append((prev, cur))
    while runs and not runs[0][0]:
        runs.pop(0)
    while runs and not runs[-1][0]:
        runs.pop()
    module = min(r for _, r in runs)
    units = []
    for is_bar, r in runs:
        u = round(r / module)
        assert abs(r - u * module) <= module * 0.25, "bad module grid"
        units.extend([1 if is_bar else 0] * u)
    bits = "".join(map(str, units))
    stop_len = len(STOP_FULL)
    n = (len(bits) - stop_len) // 11
    assert n * 11 + stop_len == len(bits), "bad symbol grid"
    syms = [bits[i * 11:(i + 1) * 11] for i in range(n)]
    assert bits[n * 11:] == STOP_FULL, "bad stop pattern"
    table = {code: i for i, code in enumerate(CODES)}
    values = [table[s] for s in syms]
    assert values[0] == START_B, "bad start symbol"
    check = (START_B + sum((i + 1) * v for i, v in enumerate(values[1:-1]))) % 103
    assert check == values[-1], "checksum mismatch"
    inv = {v: k for k, v in CHARSET_B.items()}
    return "".join(inv[v] for v in values[1:-1])


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "handout/receipt.png"
    px, w, h = read_png_rgb(path)
    up = rotate180(px, w, h)
    y0, y1 = find_band(up, w, h)
    print(f"barcode band: rows {y0}-{y1} (receipt was upside down, rotated back)")
    print(decode_row(up, w, (y0 + y1) // 2))


if __name__ == "__main__":
    main()

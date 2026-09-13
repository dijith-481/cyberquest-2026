#!/usr/bin/env python3
"""Nothing to Declare — reference solver (stdlib only).

1. Open passport.png as a ZIP, read border_control.db + INSPECTION_FORMAT.txt.
2. OCR the MRZ out of the PNG pixels (exact template match against the
   generator's 5x7 font — no external OCR needed).
3. SHA256(document_number) -> row lookup, XOR with
   SHA256(b"border-control:" + document_number) -> report.

Usage:  python3 admin/solve.py handout/passport.png
"""

import hashlib
import sqlite3
import struct
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "deployment"))
from generate import (  # noqa: E402
    FONT,
    INK,
    MRZ_BG,
    MRZ_LEN,
    MRZ_SCALE,
    MRZ_X0,
    MRZ_Y1,
    MRZ_Y2,
)

CANDIDATES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789< "


def read_png_rgb(path: str):
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    off = 8
    w = h = None
    ctype = bitd = None
    idat = bytearray()
    while off < len(data):
        (ln,) = struct.unpack(">I", data[off:off + 4])
        typ = data[off + 4:off + 8]
        body = data[off + 8:off + 8 + ln]
        if typ == b"IHDR":
            w, h, bitd, ctype, _, _, _ = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        off += 12 + ln
    assert bitd == 8 and ctype == 2, f"unexpected PNG type {bitd}/{ctype}"
    raw = zlib.decompress(bytes(idat))
    stride = w * 3 + 1
    px = bytearray(w * h * 3)
    for y in range(h):
        f = raw[y * stride]
        assert f == 0, f"unexpected filter {f}"
        px[y * w * 3:(y + 1) * w * 3] = raw[y * stride + 1:(y + 1) * stride]
    return px, w, h


def _pix(px, w, x, y):
    o = (y * w + x) * 3
    return (px[o], px[o + 1], px[o + 2])


def ocr_char(px, w, x0, y0):
    best, best_score = "?", -1
    for ch in CANDIDATES:
        glyph = FONT.get(ch, FONT[" "])
        score = 0
        total = 0
        ok = True
        for row in range(7):
            for col in range(5):
                want_ink = glyph[row][col] == "#"
                for dy in range(MRZ_SCALE):
                    for dx in range(MRZ_SCALE):
                        got = _pix(px, w, x0 + col * MRZ_SCALE + dx, y0 + row * MRZ_SCALE + dy)
                        want = INK if want_ink else MRZ_BG
                        total += 1
                        if tuple(got) == tuple(want):
                            score += 1
                        else:
                            ok = False
        if ok:
            return ch  # exact match — unambiguous by construction
        if score > best_score:
            best_score, best = score, ch
    return best


def ocr_mrz(path: str):
    px, w, _ = read_png_rgb(path)
    lines = []
    for y0 in (MRZ_Y1, MRZ_Y2):
        s = ""
        for i in range(MRZ_LEN):
            s += ocr_char(px, w, MRZ_X0 + i * 6 * MRZ_SCALE, y0)
        lines.append(s)
    return lines


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "handout/passport.png"
    l1, l2 = ocr_mrz(path)
    print(f"MRZ line 1: {l1}")
    print(f"MRZ line 2: {l2}")
    doc = l2.split("<")[0]
    assert doc.startswith("CQP") and len(doc) == 7, f"bad doc number {doc!r}"
    print(f"document: {doc}")

    with zipfile.ZipFile(path) as z:
        db_bytes = z.read("border_control.db")

    with tempfile.NamedTemporaryFile(delete=False) as t:
        t.write(db_bytes)
        name = t.name
    con = sqlite3.connect(name)
    h = hashlib.sha256(doc.encode()).hexdigest()
    row = con.execute(
        "SELECT sealed_note FROM inspection_records WHERE passport_hash=?", (h,)
    ).fetchone()
    con.close()
    assert row, "no record for this document hash"
    key = hashlib.sha256(b"border-control:" + doc.encode()).digest()
    ct = row[0]
    pt = bytes(v ^ key[i % 32] for i, v in enumerate(ct)).decode()
    print(pt, end="" if pt.endswith("\n") else "\n")


if __name__ == "__main__":
    main()

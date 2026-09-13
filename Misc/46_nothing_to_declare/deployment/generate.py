#!/usr/bin/env python3
"""Nothing to Declare — seeded generator for Misc slot 46.

Builds a PNG/ZIP polyglot passport:

  png (IHDR..IEND) + zip (border_control.db + INSPECTION_FORMAT.txt)

The PNG is rendered stdlib-only (no Pillow): a block 5x7 font on an
RGB canvas, encoded as 8-bit truecolor with filter 0. Any lenient image
viewer stops at IEND; zipfile finds the central directory at the tail.

  python3 deployment/generate.py --seed 46 --flag 'cyber_quest{...}' --out handout/passport.png
"""

from __future__ import annotations

import argparse
import hashlib
import random
import sqlite3
import struct
import tempfile
import zipfile
import zlib
from pathlib import Path

DOCUMENT_NUMBER = "CQP0427"
HOLDER_NAME = "ALICE PACKET"
SURNAME = "PACKET"
GIVEN = "ALICE"

W, H = 960, 600

BG = (235, 240, 236)
CARD = (242, 245, 240)
INK = (20, 30, 30)
MUTED = (90, 100, 95)
BORDER = (30, 50, 45)
PHOTO_BG = (195, 205, 200)
PHOTO_INK = (60, 75, 70)
MRZ_BG = (220, 225, 218)
ACCENT = (120, 50, 50)
SMALL_LBL = (90, 100, 95)

# MRZ layout (must stay in sync with admin/solve.py OCR)
MRZ_X0 = 60
MRZ_Y1 = 478
MRZ_Y2 = 518
MRZ_SCALE = 2
MRZ_LEN = 44

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 strings of 5 chars ('#' / '.'). Human-readable on canvas,
# machine-readable by the reference solver (exact template match).

FONT: dict[str, list[str]] = {
 "A": [".###.","#...#","#...#","#####","#...#","#...#","#...#"],
 "B": ["####.","#...#","#...#","####.","#...#","#...#","####."],
 "C": [".####","#....","#....","#....","#....","#....",".####"],
 "D": ["####.","#...#","#...#","#...#","#...#","#...#","####."],
 "E": ["#####","#....","#....","####.","#....","#....","#####"],
 "F": ["#####","#....","#....","####.","#....","#....","#...."],
 "G": [".####","#....","#....","#.###","#...#","#...#",".###."],
 "H": ["#...#","#...#","#...#","#####","#...#","#...#","#...#"],
 "I": ["#####","..#..","..#..","..#..","..#..","..#..","#####"],
 "J": ["..###","...#.","...#.","...#.","...#.","#..#.",".##.."],
 "K": ["#...#","#..#.","#.#..","##...","#.#..","#..#.","#...#"],
 "L": ["#....","#....","#....","#....","#....","#....","#####"],
 "M": ["#...#","##.##","#.#.#","#.#.#","#...#","#...#","#...#"],
 "N": ["#...#","##..#","##..#","#.#.#","#..##","#..##","#...#"],
 "O": [".###.","#...#","#...#","#...#","#...#","#...#",".###."],
 "P": ["####.","#...#","#...#","####.","#....","#....","#...."],
 "Q": [".###.","#...#","#...#","#...#","#.#.#","#..#.",".##.#"],
 "R": ["####.","#...#","#...#","####.","#.#..","#..#.","#...#"],
 "S": [".####","#....","#....",".###.","....#","....#","####."],
 "T": ["#####","..#..","..#..","..#..","..#..","..#..","..#.."],
 "U": ["#...#","#...#","#...#","#...#","#...#","#...#",".###."],
 "V": ["#...#","#...#","#...#","#...#","#...#",".#.#.","..#.."],
 "W": ["#...#","#...#","#...#","#.#.#","#.#.#","##.##","#...#"],
 "X": ["#...#","#...#",".#.#.","..#..",".#.#.","#...#","#...#"],
 "Y": ["#...#","#...#",".#.#.","..#..","..#..","..#..","..#.."],
 "Z": ["#####","....#","...#.","..#..",".#...","#....","#####"],
 "0": [".###.","#..##","#.#.#","#.#.#","##..#","#...#",".###."],
 "1": ["..#..",".##..","..#..","..#..","..#..","..#..",".###."],
 "2": [".###.","#...#","....#","...#.","..#..",".#...","#####"],
 "3": ["#####","...#.","..#..","...#.","....#","#...#",".###."],
 "4": ["...#.","..##.",".#.#.","#..#.","#####","...#.","...#."],
 "5": ["#####","#....","####.","....#","....#","#...#",".###."],
 "6": ["..##.",".#...","#....","####.","#...#","#...#",".###."],
 "7": ["#####","....#","...#.","..#..","..#..","..#..","..#.."],
 "8": [".###.","#...#","#...#",".###.","#...#","#...#",".###."],
 "9": [".###.","#...#","#...#",".####","....#","...#.",".##.."],
 "<": ["...#.","..#..",".#...","#....",".#...","..#..","...#."],
 " ": [".....",".....",".....",".....",".....",".....","....."],
 "-": [".....",".....",".....","#####",".....",".....","....."],
 "/": ["....#","....#","...#.","..#..",".#...","#....","#...."],
 ".": [".....",".....",".....",".....",".....",".##..",".##.."],
 ":": [".....",".##..",".##..",".....",".##..",".##..","....."],
 "(": ["...#.","..#..",".#...",".#...",".#...","..#..","...#."],
 ")": [".#...","..#..","...#.","...#.","...#.","..#..",".#..."],
 "_": [".....",".....",".....",".....",".....",".....","#####"],
}


def mrz_lines(doc: str = DOCUMENT_NUMBER) -> tuple[str, str]:
    l1 = "P<CYBPACKET<<ALICE" + "<" * (MRZ_LEN - len("P<CYBPACKET<<ALICE"))
    raw2 = f"{doc}<CYB010101"
    l2 = raw2 + "<" * (MRZ_LEN - len(raw2))
    assert len(l1) == MRZ_LEN and len(l2) == MRZ_LEN
    return l1, l2


# ---------------------------------------------------------------- canvas

def _new_canvas():
    px = bytearray(W * H * 3)
    for i in range(W * H):
        px[i * 3] = BG[0]
        px[i * 3 + 1] = BG[1]
        px[i * 3 + 2] = BG[2]
    return px


def _set(px, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        o = (y * W + x) * 3
        px[o], px[o + 1], px[o + 2] = color


def _fill_rect(px, x0, y0, x1, y1, color):
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W - 1, x1), min(H - 1, y1)
    for y in range(y0, y1 + 1):
        base = y * W * 3
        for x in range(x0, x1 + 1):
            o = base + x * 3
            px[o], px[o + 1], px[o + 2] = color


def _rect_outline(px, x0, y0, x1, y1, color, w=3):
    for t in range(w):
        for x in range(x0 + t, x1 - t + 1):
            _set(px, x, y0 + t, color)
            _set(px, x, y1 - t, color)
        for y in range(y0 + t, y1 - t + 1):
            _set(px, x0 + t, y, color)
            _set(px, x1 - t, y, color)


def _fill_circle(px, cx, cy, r, color):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r:
                _set(px, x, y, color)


def draw_text(px, x, y, s: str, scale: int, color):
    s = s.upper()
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == "#":
                    for dy in range(scale):
                        for dx in range(scale):
                            _set(px, cx + col * scale + dx, y + row * scale + dy, color)
        cx += 6 * scale
    return cx


def text_width(s: str, scale: int) -> int:
    return len(s) * 6 * scale


def build_passport_png() -> bytes:
    px = _new_canvas()
    # card
    _fill_rect(px, 30, 30, W - 31, H - 31, CARD)
    _rect_outline(px, 30, 30, W - 31, H - 31, BORDER, 3)

    # subtle guilloche lines so the page does not look flat
    for gy in range(150, 440, 10):
        for gx in range(40, W - 40):
            _set(px, gx, gy, (231, 236, 229))

    draw_text(px, 70, 60, "REPUBLIC OF CYBERLAND", 3, INK)
    draw_text(px, 72, 108, "P A S S P O R T", 2, INK)
    draw_text(px, 72, 130, "IMPORT LOT 07 - RECEIVING", 1, MUTED)

    # photograph: neutral silhouette, no text
    _fill_rect(px, 80, 170, 250, 360, PHOTO_BG)
    _rect_outline(px, 80, 170, 250, 360, PHOTO_INK, 2)
    _fill_circle(px, 165, 242, 34, (105, 115, 110))
    _fill_rect(px, 108, 292, 222, 360, (105, 115, 110))

    # receiving stamp over the photo corner, like a real entry mark
    _rect_outline(px, 140, 296, 270, 364, ACCENT, 2)
    draw_text(px, 150, 310, "OE RECEIVING", 1, ACCENT)
    draw_text(px, 160, 330, "IMPORT 07", 1, ACCENT)

    # data page: two columns like a real passport
    left = [
        ("SURNAME", SURNAME),
        ("GIVEN NAMES", GIVEN),
        ("NATIONALITY", "CYBERLAND"),
        ("DOCUMENT NO", DOCUMENT_NUMBER),
    ]
    right = [
        ("SEX", "F"),
        ("DATE OF BIRTH", "01 JAN 1990"),
        ("DATE OF EXPIRY", "01 JAN 2035"),
        ("AUTHORITY", "MINISTRY OF INTERIOR"),
    ]
    y = 165
    for (ll, lv), (rl, rv) in zip(left, right):
        draw_text(px, 300, y, ll, 1, SMALL_LBL)
        draw_text(px, 300, y + 14, lv, 2, INK)
        draw_text(px, 640, y, rl, 1, SMALL_LBL)
        draw_text(px, 640, y + 14, rv, 2, INK)
        y += 62
    draw_text(px, 300, y, "TYPE", 1, SMALL_LBL)
    draw_text(px, 300, y + 14, "P", 2, INK)
    draw_text(px, 640, y, "COUNTRY CODE", 1, SMALL_LBL)
    draw_text(px, 640, y + 14, "CYB", 2, INK)

    # mrz band
    _fill_rect(px, 45, 445, W - 46, 560, MRZ_BG)
    l1, l2 = mrz_lines()
    draw_text(px, MRZ_X0, MRZ_Y1, l1, MRZ_SCALE, INK)
    draw_text(px, MRZ_X0, MRZ_Y2, l2, MRZ_SCALE, INK)

    # encode truecolor PNG, filter 0
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(px[y * W * 3:(y + 1) * W * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ: bytes, data: bytes) -> bytes:
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", comp) + chunk(b"IEND", b"")


# ---------------------------------------------------------------- crypto/db

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def xor_repeat(data: bytes, key: bytes) -> bytes:
    return bytes(v ^ key[i % len(key)] for i, v in enumerate(data))


def inspection_key(document_number: str) -> bytes:
    return hashlib.sha256(b"border-control:" + document_number.encode()).digest()


def target_plaintext(flag: str) -> bytes:
    return (
        "SECONDARY INSPECTION REPORT\n"
        "\n"
        f"Subject: {HOLDER_NAME}\n"
        f"Document: {DOCUMENT_NUMBER}\n"
        "Checkpoint: TERMINAL-07\n"
        "Status: CLEARED\n"
        "Importer: ORDINARY ENGINEERING\n"
        "\n"
        "Recovered evidence:\n"
    ).encode() + flag.encode() + b"\n"


INSPECTION_FORMAT = """\
ordinary engineering -- receiving
ENTRY-DESK OFFLINE FORMAT v3
===============================================

Database:
    border_control.db

RECORD LOOKUP
-------------

The inspection system does not store raw document
numbers.

passport_hash = SHA256(document_number)

The document number must be taken from the
machine-readable region of the inspected document.

Remove '<' padding before hashing.

SEALED NOTES
------------

Inspection reports are stored using the legacy
checkpoint obfuscation mechanism.

key = SHA256(b"border-control:" + document_number)

The 32-byte key repeats across the entire sealed note.

plaintext[i] = sealed_note[i] XOR key[i % 32]

NOTE
----

Raw passport numbers are deliberately absent from
this archive.

The physical document remains the authoritative
source.

Filed by entry-desk. Everything here is normal.
"""


def build_database(flag: str, seed: int) -> bytes:
    rng = random.Random(f"{seed}|border-control-db")
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "border_control.db"
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE inspection_records (
                passport_hash TEXT PRIMARY KEY,
                checkpoint TEXT NOT NULL,
                status TEXT NOT NULL,
                sealed_note BLOB NOT NULL
            )
            """
        )
        target_hash = sha256_hex(DOCUMENT_NUMBER.encode())
        ct = xor_repeat(target_plaintext(flag), inspection_key(DOCUMENT_NUMBER))
        cur.execute(
            "INSERT INTO inspection_records VALUES (?,?,?,?)",
            (target_hash, "TERMINAL-07", "SECONDARY", ct),
        )
        seen = {target_hash}
        for _ in range(63):
            while True:
                fh = bytes(rng.getrandbits(8) for _ in range(32)).hex()
                # keep namespace disjoint from real SHA256 hex space statistically;
                # just avoid accidental collision with target
                if fh not in seen:
                    seen.add(fh)
                    break
            ln = 90 + rng.randrange(100)
            blob = bytes(rng.getrandbits(8) for _ in range(ln))
            cur.execute(
                "INSERT INTO inspection_records VALUES (?,?,?,?)",
                (
                    fh,
                    f"TERMINAL-{rng.randrange(20):02d}",
                    rng.choice(["CLEARED", "SECONDARY", "REJECTED", "MANUAL"]),
                    blob,
                ),
            )
        con.commit()
        con.close()
        return db_path.read_bytes()


def build_zip(flag: str, seed: int) -> bytes:
    import io

    db = build_database(flag, seed)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in (
            ("INSPECTION_FORMAT.txt", INSPECTION_FORMAT.encode()),
            ("border_control.db", db),
        ):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 13, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.compress_level = 9
            z.writestr(info, data)
    return buf.getvalue()


def build_polyglot(flag: str, seed: int) -> bytes:
    return build_passport_png() + build_zip(flag, seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--flag", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    payload = build_polyglot(args.flag, args.seed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_bytes(payload)
    print(f"wrote {args.out} ({len(payload)} bytes, seed {args.seed})")


if __name__ == "__main__":
    main()

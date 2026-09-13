#!/usr/bin/env python3
"""No Refunds — seeded generator for Misc slot 47.

Builds `receipt.png`: a thermal-paper-style shop receipt (block 5x7
font, stdlib-only PNG) with a real Code 128-B barcode encoding the
flag. The whole receipt is rendered upright and then rotated 180
degrees, so the handout arrives upside down — barcode included.

  python3 deployment/generate.py --seed 47 --flag 'cyber_quest{...}' --out handout/receipt.png

The Code 128 patterns below match the symbology specification
(Start B = 104, weighted-mod-103 checksum, Stop = 11000111010).
"""

from __future__ import annotations

import argparse
import random
import struct
import zlib
from pathlib import Path

W, H = 960, 1400

PAPER = (248, 246, 238)
INK = (15, 15, 15)
WHITE = (255, 255, 255)

MODULE_W = 2
BAR_H = 120
QUIET_MODULES = 10

# Barcode x placement (informational; the solver auto-locates the band).
BAR_X0 = 56
BAR_Y = 0          # filled in by build_receipt() for the upright layout

# ---------------------------------------------------------------- 5x7 font
# Glyphs: 7 strings of 5 chars ('#' / '.'). Receipt copy is uppercase.

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
 " ": [".....",".....",".....",".....",".....",".....","....."],
 "-": [".....",".....",".....","#####",".....",".....","....."],
 "/": ["....#","....#","...#.","..#..",".#...","#....","#...."],
 ".": [".....",".....",".....",".....",".....",".##..",".##.."],
 ":": [".....",".##..",".##..",".....",".##..",".##..","....."],
 "*": [".....","#...#",".#.#.","..#..",".#.#.","#...#","....."],
 "=": [".....",".....","#####",".....","#####",".....","....."],
 "?": ["..##.","...#.","...#.","..#..","..#..",".....","..#.."],
 "!": ["..#..","..#..","..#..","..#..","..#..",".....","..#.."],
 "+": [".....","..#..","..#..","#####","..#..","..#..","....."],
 "%": ["#...#","#..#.","..#..",".#...",".#..#","#...#","....."],
}

# ---------------------------------------------------------------- Code 128
# Bit patterns ('1' = bar), values 0-105, plus the 13-module stop.
# Start B = 104. Checksum = (start + sum(pos * code)) mod 103.

CODES = (
 "11011001100","11001101100","11001100110","10010011000","10010001100",
 "10001001100","10011001000","10011000100","10001100100","11001001000",
 "11001000100","11000100100","10110011100","10011011100","10011001110",
 "10111001100","10011101100","10011100110","11001110010","11001011100",
 "11001001110","11011100100","11001110100","11101101110","11101001100",
 "11100101100","11100100110","11101100100","11100110100","11100110010",
 "11011011000","11011000110","11000110110","10100011000","10001011000",
 "10001000110","10110001000","10001101000","10001100010","11010001000",
 "11000101000","11000100010","10110111000","10110001110","10001101110",
 "10111011000","10111000110","10001110110","11101110110","11010001110",
 "11000101110","11011101000","11011100010","11011101110","11101011000",
 "11101000110","11100010110","11101101000","11101100010","11100011010",
 "11101111010","11001000010","11110001010","10100110000","10100001100",
 "10010110000","10010000110","10000101100","10000100110","10110010000",
 "10110000100","10011010000","10011000010","10000110100","10000110010",
 "11000010010","11001010000","11110111010","11000010100","10001111010",
 "10100111100","10010111100","10010011110","10111100100","10011110100",
 "10011110010","11110100100","11110010100","11110010010","11011011110",
 "11011110110","11110110110","10101111000","10100011110","10001011110",
 "10111101000","10111100010","11110101000","11110100010","10111011110",
 "10111101110","11101011110","11110101110","11010000100","11010010000",
 "11010011100",
)
STOP = "11000111010"
STOP_FULL = STOP + "11"  # stop character is 13 modules wide incl. termination bars
START_B = 104

_COMMON = (
 " ", "!", '"', "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-",
 ".", "/", *tuple("0123456789"), ":", ";", "<", "=", ">", "?",
 "@", *tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), "[", "\\", "]", "^", "_",
)
_B_EXTRA = ("`", *tuple("abcdefghijklmnopqrstuvwxyz"), "{", "|", "}", "~", "\x7f")
CHARSET_B = {ch: i for i, ch in enumerate((*_COMMON, *_B_EXTRA))}


def encode_code128_b(payload: str) -> tuple[list[int], str]:
    """Return (symbol values incl. start+checksum, full bit string)."""
    values = []
    for ch in payload:
        if ch not in CHARSET_B:
            raise ValueError(f"char {ch!r} not in Code 128-B")
        values.append(CHARSET_B[ch])
    checksum = (START_B + sum((i + 1) * v for i, v in enumerate(values))) % 103
    full_values = [START_B, *values, checksum]
    bits = "".join(CODES[v] for v in full_values) + STOP_FULL
    return full_values, bits


# ---------------------------------------------------------------- canvas

def _new_canvas():
    px = bytearray(W * H * 3)
    for i in range(W * H):
        px[i * 3] = PAPER[0]
        px[i * 3 + 1] = PAPER[1]
        px[i * 3 + 2] = PAPER[2]
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


def draw_text(px, x, y, s: str, scale: int, color=INK):
    cx = x
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is None:
            raise ValueError(f"font lacks char {ch!r}")
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == "#":
                    for dy in range(scale):
                        for dx in range(scale):
                            _set(px, cx + col * scale + dx, y + row * scale + dy, color)
        cx += 6 * scale
    return cx


def centered(px, text: str, y: int, scale: int):
    wpx = len(text) * 6 * scale - scale
    draw_text(px, (W - wpx) // 2, y, text, scale)


def receipt_lines(seed: int) -> list[tuple[str, int]]:
    rng = random.Random(f"{seed}|byte-mart")
    term = rng.randint(1, 9)
    hh = rng.randint(1, 12)
    mm = rng.randint(0, 59)
    txn = rng.randint(0, 999999)
    return [
        ("BYTE MART EXPRESS", 3),
        ("================================", 2),
        ("", 2),
        (f"TERMINAL : /DEV/TTY{term}", 2),
        ("CASHIER : ROOT", 2),
        ("DATE : 13/09/2026", 2),
        (f"TIME : {hh:02d}:{mm:02d} PM", 2),
        (f"TXN : {txn:06d}", 2),
        ("", 2),
        ("--------------------------------", 2),
        ("", 2),
        ("1 X ENERGY DRINK RS 90.00", 2),
        ("2 X INSTANT NOODLES RS 80.00", 2),
        ("1 X USB-C CABLE RS 249.00", 2),
        ("1 X EMOTIONAL SUPPORT", 2),
        ("DEBUGGER RS 0.00", 2),
        ("1 X WORKS ON MY MACHINE", 2),
        ("STICKER RS 20.00", 2),
        ("", 2),
        ("--------------------------------", 2),
        ("", 2),
        ("SUBTOTAL RS 439.00", 2),
        ("BUG TAX RS 13.37", 2),
        ("TOTAL RS 452.37", 2),
        ("", 2),
        ("PAYMENT : CONTACTLESS", 2),
        ("STATUS : APPROVED*", 2),
        ("*PROBABLY", 2),
        ("", 2),
        ("--------------------------------", 2),
        ("", 2),
        ("NO REFUNDS", 2),
        ("NO EXCHANGES", 2),
        ("NO SEGFAULTS", 2),
        ("", 2),
        ("--------------------------------", 2),
        ("", 2),
        ("THANK YOU FOR SHOPPING", 2),
        ("WITH BYTE MART", 2),
        ("PLEASE KEEP RECEIPT", 2),
        ("", 2),
        ("--------------------------------", 2),
        ("__BARCODE__", 0),
        ("", 2),
        ("IF THIS DOES NOT SCAN", 2),
        ("TRY ANOTHER ANGLE", 2),
        ("ORIENTATION : ???", 2),
    ]


def draw_barcode(px, x0: int, y0: int, bits: str, module_w: int):
    """Draw bars; returns pixel height used. Quiet zone included."""
    pad = 12
    total_w = len(bits) * module_w
    _fill_rect(px, x0, y0, x0 + total_w - 1, y0 + pad + BAR_H + pad, WHITE)
    for i, b in enumerate(bits):
        if b == "1":
            for dx in range(module_w):
                for dy in range(BAR_H):
                    _set(px, x0 + i * module_w + dx, y0 + pad + dy, INK)
    return pad + BAR_H + pad


def build_receipt_png(flag: str, seed: int) -> bytes:
    global BAR_Y
    _, bits = encode_code128_b(flag)
    module_w = MODULE_W
    if BAR_X0 + len(bits) * module_w > W - 20:
        module_w = 1
    assert BAR_X0 + len(bits) * module_w <= W - 20, "flag too long for receipt"

    px = _new_canvas()
    y = 60
    barcode_y = None
    for text, scale in receipt_lines(seed):
        if text == "__BARCODE__":
            barcode_y = y + 10
            y += 10 + draw_barcode(px, BAR_X0, barcode_y, bits, module_w) + 10
            continue
        if text:
            centered(px, text, y, scale)
        y += 7 * scale + 8 if scale else 0
    assert y < H - 40, f"receipt overflow: y={y}"
    BAR_Y = barcode_y if barcode_y is not None else 0

    # The joke: the whole receipt ships upside down.
    rot = bytearray(len(px))
    for yy in range(H):
        for xx in range(W):
            s = ((H - 1 - yy) * W + (W - 1 - xx)) * 3
            d = (yy * W + xx) * 3
            rot[d], rot[d + 1], rot[d + 2] = px[s], px[s + 1], px[s + 2]

    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw.extend(rot[yy * W * 3:(yy + 1) * W * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ: bytes, data: bytes) -> bytes:
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", comp) + chunk(b"IEND", b"")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--flag", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data = build_receipt_png(args.flag, args.seed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_bytes(data)
    print(f"wrote {args.out} ({len(data)} bytes, seed {args.seed}, bar_y={BAR_Y})")


if __name__ == "__main__":
    main()

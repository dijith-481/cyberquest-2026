#!/usr/bin/env python3
"""gridlock — deterministic handout generator (stdlib only).

Builds the brand asset the players receive:

  handout/brand_memo.txt   the facilities/brand memo (deadpan, no spoilers)
  handout/pipeline.py      the asset pipeline, key redacted
  handout/logo.enc.bmp     the company logo, AES-128-ECB encrypted

The logo is rendered in-code with a tiny 5x7 pixel font, packed as a
24-bit BMP, and its pixel bytes are encrypted with AES-128-ECB while the
54-byte header is left intact so thumbnailers keep working. The image is
480x360: 480*4 = 1920 bytes per row (a multiple of 16, so every row starts on
a block boundary) and 480*720*4 = 1382400 bytes of pixel data (likewise
a multiple of 16, so no padding is added).

    python3 make_handout.py

The zip handed to players is built with:  zip -j 25_gridlock.zip handout/*
"""

import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{3cb_k33ps_3v3ry_sh4p3_7e4a19}"
KEY = bytes.fromhex("8f2c4a91d6e3b507f1a8c9d4e6b30257")

W, H = 480, 720

# NOTE ON THE LAYOUT (this is the whole challenge): AES-ECB encrypts the
# pixel stream in independent 16-byte blocks, so two blocks only produce
# the same ciphertext when their 16 bytes match exactly. Each image row is
# 480*3 = 1440 bytes = 90 blocks, so every row starts on a block boundary,
# and every horizontal feature is placed at x a multiple of 16 with a
# width that is a whole number of blocks (16 px = 48 bytes = 3 blocks).
# Identical letters therefore encrypt to identical block runs, and the
# shapes survive encryption as a blocky ghost. A layout that ignored the
# block grid would encrypt to pure noise.

# --------------------------------------------------------------------------
# minimal AES-128 (encrypt only), validated against the FIPS-197 appendix B
# vector. Vendored so the generator stays stdlib-only.
# --------------------------------------------------------------------------

_SBOX = (
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
)
_RCON = (0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36)


def _xtime(x):
    return ((x << 1) ^ 0x11B) & 0xFF if x & 0x80 else (x << 1) & 0xFF


def _mul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = _xtime(a)
        b >>= 1
    return r


_M2 = [_mul(i, 2) for i in range(256)]
_M3 = [_mul(i, 3) for i in range(256)]


def _expand(key):
    rk = list(key)
    for i in range(10):
        prev = rk[-16:]
        t = [_SBOX[prev[13]], _SBOX[prev[14]], _SBOX[prev[15]], _SBOX[prev[12]]]
        t[0] ^= _RCON[i]
        for j in range(4):
            w = [a ^ b for a, b in zip(t, prev[j * 4:j * 4 + 4])]
            rk += w
            t = w
    return [bytes(rk[i * 16:(i + 1) * 16]) for i in range(11)]


def _enc_block(b, rk):
    s = [a ^ c for a, c in zip(b, rk[0])]
    for r in range(1, 10):
        s = [_SBOX[x] for x in s]
        s = [s[0],s[5],s[10],s[15],s[4],s[9],s[14],s[3],s[8],s[13],s[2],s[7],s[12],s[1],s[6],s[11]]
        for c in range(4):
            a0, a1, a2, a3 = s[4 * c:4 * c + 4]
            s[4 * c:4 * c + 4] = [_M2[a0]^_M3[a1]^a2^a3, a0^_M2[a1]^_M3[a2]^a3,
                                 a0^a1^_M2[a2]^_M3[a3], _M3[a0]^a1^a2^_M2[a3]]
        s = [a ^ c for a, c in zip(s, rk[r])]
    s = [_SBOX[x] for x in s]
    s = [s[0],s[5],s[10],s[15],s[4],s[9],s[14],s[3],s[8],s[13],s[2],s[7],s[12],s[1],s[6],s[11]]
    return bytes(a ^ c for a, c in zip(s, rk[10]))


def aes_ecb_encrypt(data, key):
    assert len(data) % 16 == 0
    rk = _expand(key)
    return b"".join(_enc_block(data[i:i + 16], rk) for i in range(0, len(data), 16))


# --------------------------------------------------------------------------
# tiny 5x7 pixel font ('#' ink, '.' empty)
# --------------------------------------------------------------------------

_FONT = {
'A': (".###.","#...#","#...#","#####","#...#","#...#","#...#"),
'B': ("####.","#...#","#...#","####.","#...#","#...#","####."),
'C': (".####","#....","#....","#....","#....","#....",".####"),
'D': ("####.","#...#","#...#","#...#","#...#","#...#","####."),
'E': ("#####","#....","#....","####.","#....","#....","#####"),
'F': ("#####","#....","#....","####.","#....","#....","#...."),
'G': (".####","#....","#....","#.###","#...#","#...#",".###."),
'H': ("#...#","#...#","#...#","#####","#...#","#...#","#...#"),
'I': ("#####","..#..","..#..","..#..","..#..","..#..","#####"),
'J': ("..###","...#.","...#.","...#.","...#.","#..#.",".##.."),
'K': ("#...#","#...#","#..#.","##...","#..#.","#...#","#...#"),
'L': ("#....","#....","#....","#....","#....","#....","#####"),
'M': ("#...#","#####","#####","#.#.#","#...#","#...#","#...#"),
'N': ("#...#","##..#","##..#","#.#.#","#..##","#..##","#...#"),
'O': (".###.","#...#","#...#","#...#","#...#","#...#",".###."),
'P': ("####.","#...#","#...#","####.","#....","#....","#...."),
'Q': (".###.","#...#","#...#","#...#","#.#.#","#..#.",".##.#"),
'R': ("####.","#...#","#...#","####.","#..#.","#...#","#...#"),
'S': (".####","#....","#....",".###.","....#","....#","####."),
'T': ("#####","..#..","..#..","..#..","..#..","..#..","..#.."),
'U': ("#...#","#...#","#...#","#...#","#...#","#...#",".###."),
'V': ("#...#","#...#","#...#","#...#","#...#",".#.#.","..#.."),
'W': ("#...#","#...#","#...#","#.#.#","#####","#####","#...#"),
'X': ("#...#","#...#",".#.#.","..#..",".#.#.","#...#","#...#"),
'Y': ("#...#","#...#",".#.#.","..#..","..#..","..#..","..#.."),
'Z': ("#####","....#","...#.","..#..",".#...","#....","#####"),
'0': (".###.","#..##","#.#.#","#.#.#","##..#","#...#",".###."),
'1': ("..#..",".##..","..#..","..#..","..#..","..#..","#####"),
'2': (".###.","#...#","....#","...#.","..#..",".#...","#####"),
'3': ("####.","....#","....#",".###.","....#","#...#",".###."),
'4': ("...#.","..##.",".#.#.","#..#.","#####","...#.","...#."),
'5': ("#####","#....","####.","....#","....#","#...#",".###."),
'6': (".###.","#....","#....","####.","#...#","#...#",".###."),
'7': ("#####","....#","...#.","..#..",".#...",".#...",".#..."),
'8': (".###.","#...#","#...#",".###.","#...#","#...#",".###."),
'9': (".###.","#...#","#...#",".####","....#","....#",".###."),
'a': (".....",".....",".###.","....#",".####","#...#",".####"),
'b': ("#....","#....","####.","#...#","#...#","#...#","####."),
'c': (".....",".....",".####","#....","#....","#....",".####"),
'd': ("....#","....#",".####","#...#","#...#","#...#",".####"),
'e': (".....",".....",".###.","#...#","#####","#....",".###."),
'h': ("#....","#....","#.##.","#..#.","#...#","#...#","#...#"),
'k': ("#....","#....","#..#.","#.#..","##...","#..#.","#..#."),
'm': (".....",".....","##.#.","#.#.#","#.#.#","#...#","#...#"),
'p': (".....",".....","####.","#...#","####.","#....","#...."),
'q': (".....",".....",".####","#...#","#...#",".####","....#"),
'r': (".....",".....","#.##.","#..#.","#....","#....","#...."),
's': (".....",".....",".####","#....",".###.","....#","####."),
't': ("..#..","..#..","#####","..#..","..#..","..#..",".###."),
'u': (".....",".....","#...#","#...#","#...#","#...#",".####"),
'v': (".....",".....","#...#","#...#","#...#",".#.#.","..#.."),
'y': (".....",".....","#...#","#...#",".#.#.","..#..","..#.."),
' ': (".....",".....",".....",".....",".....",".....","....."),
'_': (".....",".....",".....",".....",".....",".....","#####"),
'{': ("...#.","..#..","..#..",".##..","..#..","..#..","...#."),
'}': (".#...","..#..","..#..","..##.","..#..","..#..",".#..."),
'.': (".....",".....",".....",".....",".....",".##..",".##.."),
'-': (".....",".....",".....",".....","#####",".....","....."),
'/': ("....#","....#","...#.","...#.","..#..","..#..",".#..."),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


# --------------------------------------------------------------------------
# canvas helpers (top-down RGB)
# --------------------------------------------------------------------------

WHITE = (255, 255, 255, 255)
BLACK = (10, 10, 10, 255)
LIGHT = (216, 216, 216, 255)


class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 4)
        for i in range(w * h):
            self.px[4 * i:4 * i + 4] = bytes(WHITE)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                o = (y * self.w + x) * 4
                self.px[o:o + 4] = bytes(color)

    def text(self, s, x, y, scale, color):
        for ci, ch in enumerate(s):
            glyph = _FONT[ch]  # KeyError here means the font needs the glyph
            for gy in range(7):
                for gx in range(5):
                    if glyph[gy][gx] == "#":
                        self.rect(x + ci * 6 * scale + gx * scale,
                                  y + gy * scale,
                                  x + ci * 6 * scale + gx * scale + scale,
                                  y + gy * scale + scale, color)

    def centered_text(self, s, y, scale, color):
        self.text(s, (self.w - text_width(s, scale)) // 2, y, scale, color)


def render_logo():
    cv = Canvas(W, H)
    cv.rect(0, 0, W, H, WHITE)
    # outer border
    cv.rect(0, 0, W, 6, BLACK)
    cv.rect(0, H - 6, W, H, BLACK)
    cv.rect(0, 0, 6, H, BLACK)
    cv.rect(W - 6, 0, W, H, BLACK)
    # header bar with the company mark, giant so it survives as a ghost
    cv.rect(6, 6, W - 6, 70, BLACK)
    cv.text("OE", 192, 10, 8, WHITE)
    # grid field: 6 x 3 squares, 64 px wide (3 blocks), alternating fills,
    # heavy gridlines. The alternating fills are long runs of identical
    # blocks, which is exactly what ECB cannot hide.
    gx0, gy0 = 48, 78
    cols, rows, cw, ch = 6, 3, 64, 48
    for r in range(rows):
        for c in range(cols):
            fill = LIGHT if (r + c) % 2 else WHITE
            cv.rect(gx0 + c * cw, gy0 + r * ch,
                    gx0 + (c + 1) * cw, gy0 + (r + 1) * ch, fill)
    for c in range(cols + 1):
        cv.rect(gx0 + c * cw - 2, gy0, gx0 + c * cw + 2, gy0 + rows * ch, BLACK)
    for r in range(rows + 1):
        cv.rect(gx0, gy0 + r * ch - 2, gx0 + cols * cw, gy0 + r * ch + 2, BLACK)
    # center medallion: one solid black square
    cv.rect(176, 126, 304, 174, BLACK)
    # flag panel: the flag in 6-character rows at scale 8. Each glyph cell
    # is 48 px = 144 bytes = 9 blocks, and every row starts at x = 96
    # (288 bytes = 18 blocks), so identical letters meet identical block
    # boundaries and encrypt identically wherever they appear.
    cv.rect(30, 238, W - 30, 242, BLACK)
    cv.rect(30, 238, 34, 706, BLACK)
    cv.rect(W - 34, 238, W - 30, 706, BLACK)
    cv.rect(30, 702, W - 30, 706, BLACK)
    per_row = 6
    rows_text = [FLAG[i:i + per_row] for i in range(0, len(FLAG), per_row)]
    for i, line in enumerate(rows_text):
        cv.text(line, 96, 252 + i * 64, 8, BLACK)
    return bytes(cv.px)


def to_bmp(pixels):
    assert len(pixels) == W * H * 4
    row = W * 4
    assert row % 4 == 0 and len(pixels) % 16 == 0
    hsize, psize = 54, len(pixels)
    hdr = bytearray()
    hdr += b"BM"
    hdr += (hsize + psize).to_bytes(4, "little")
    hdr += (0).to_bytes(4, "little")
    hdr += hsize.to_bytes(4, "little")
    hdr += (40).to_bytes(4, "little")
    hdr += W.to_bytes(4, "little")
    hdr += H.to_bytes(4, "little")
    hdr += (1).to_bytes(2, "little")
    hdr += (32).to_bytes(2, "little")
    hdr += (0).to_bytes(4, "little")
    hdr += psize.to_bytes(4, "little")
    hdr += (2835).to_bytes(4, "little")
    hdr += (2835).to_bytes(4, "little")
    hdr += (0).to_bytes(4, "little")
    hdr += (0).to_bytes(4, "little")
    assert len(hdr) == 54
    body = bytearray()
    for y in range(H - 1, -1, -1):  # BMP rows are bottom-up
        body += pixels[y * row:(y + 1) * row]
    return bytes(hdr), bytes(body)


MEMO = """ORDINARY ENGINEERING - BRAND - INTERNAL MEMO 2026-11

Subject: the logo is encrypted now.

Following the incident in which the company logo appeared on a
third-party slide deck, all brand assets at rest are encrypted. The
pipeline takes the finished logo, keeps the file header intact so the
thumbnailers and the asset index keep working, and encrypts the rest
with AES-128 in ECB mode under the brand key, which lives in the
vault. The vault is locked. The vault is always locked.

Attached: the current logo (logo.enc.bmp), and the pipeline script
for the auditors. The auditors asked for the pipeline script. The
script is attached.

If the logo looks strange, do not adjust your monitor. Open it with
an image viewer. It opens fine. That is the entire point of keeping
the header intact.

- brand
"""

PIPELINE = '''"""brand asset pipeline - seal_logo.py (auditor copy).

The brand key is injected at seal time and is not part of this copy.
"""
from Crypto.Cipher import AES

HEADER = 54  # BMP file header + DIB header, left intact for thumbnailers

def seal(path_in, path_out, brand_key):
    raw = open(path_in, "rb").read()
    header, pixels = raw[:HEADER], raw[HEADER:]
    assert len(pixels) % 16 == 0, "logo pixel data is block-aligned by design"
    enc = AES.new(brand_key, AES.MODE_ECB).encrypt(pixels)
    open(path_out, "wb").write(header + enc)
    print("sealed:", path_out)
'''


def main():
    os.makedirs(HANDOUT, exist_ok=True)
    pixels = render_logo()
    header, body = to_bmp(pixels)
    sealed = header + aes_ecb_encrypt(body, KEY)
    with open(os.path.join(HANDOUT, "logo.enc.bmp"), "wb") as f:
        f.write(sealed)
    with open(os.path.join(HANDOUT, "brand_memo.txt"), "w") as f:
        f.write(MEMO)
    with open(os.path.join(HANDOUT, "pipeline.py"), "w") as f:
        f.write(PIPELINE)
    print("handout written:", os.path.normpath(HANDOUT))
    print("flag:", FLAG)
    print("pixels sha256:", hashlib.sha256(bytes(body)).hexdigest())


if __name__ == "__main__":
    main()

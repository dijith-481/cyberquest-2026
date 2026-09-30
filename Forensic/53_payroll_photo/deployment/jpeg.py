#!/usr/bin/env python3
"""Minimal baseline JPEG encoder (stdlib only, vendored).

Just enough of ITU-T T.81 to write a valid 8-bit baseline sequential
DCT image: DQT / SOF0 / DHT / SOS / entropy-coded scan / EOI, 4:4:4
(no chroma subsampling), single quantisation table, single DC/AC
Huffman pair shared by all three components.

Vendored so deployment/make_handout.py stays stdlib-only and the handout
is byte-reproducible. Not a general-purpose encoder: no progressive
mode, no restart markers, no arithmetic coding, no 4:2:0.

    from jpeg import encode
    data = encode(width, height, rgb_bytes)   # rgb_bytes = w*h*3
"""

import math
import struct

ZIGZAG = [
     0,  1,  8, 16,  9,  2,  3, 10,
    17, 24, 32, 25, 18, 11,  4,  5,
    12, 19, 26, 33, 40, 48, 41, 34,
    27, 20, 13,  6,  7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36,
    29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46,
    53, 60, 61, 54, 47, 55, 62, 63,
]

# ITU-T T.81 Annex K.1, luminance quantisation table, natural order.
QUANT_LUMA = [
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99,
]

# Annex K.3.3.1 - DC luminance
DC_BITS = [0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
DC_VALS = list(range(12))

# Annex K.3.3.2 - AC luminance
AC_BITS = [0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 0x7D]
AC_VALS = [
    0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31,
    0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
    0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52,
    0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16,
    0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A,
    0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
    0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57,
    0x58, 0x59, 0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69,
    0x6A, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x83,
    0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x92, 0x93, 0x94,
    0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3, 0xA4, 0xA5,
    0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
    0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7,
    0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8,
    0xD9, 0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8,
    0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8,
    0xF9, 0xFA,
]

_COS = [[math.cos((2 * x + 1) * u * math.pi / 16) for u in range(8)] for x in range(8)]
_C = [(1 / math.sqrt(2)) if u == 0 else 1.0 for u in range(8)]


def _build_codes(bits, vals):
    """Expand a (BITS, HUFFVAL) pair into a {value: (code, length)} map."""
    codes, code, k = {}, 0, 0
    for length in range(1, 17):
        for _ in range(bits[length - 1]):
            codes[vals[k]] = (code, length)
            code += 1
            k += 1
        code <<= 1
    return codes


_DC_CODES = _build_codes(DC_BITS, DC_VALS)
_AC_CODES = _build_codes(AC_BITS, AC_VALS)


def _magnitude(value):
    """(bit length, bit pattern) for a JPEG coefficient, per T.81 F.1.2."""
    if value == 0:
        return 0, 0
    magnitude = abs(value)
    bits = magnitude.bit_length()
    # negative values are stored as the one's complement of |value|
    return bits, (value if value > 0 else value + (1 << bits) - 1)


class _BitWriter:
    def __init__(self):
        self.out = bytearray()
        self.acc = 0
        self.n = 0

    def write(self, code, length):
        for i in range(length - 1, -1, -1):
            self.acc = (self.acc << 1) | ((code >> i) & 1)
            self.n += 1
            if self.n == 8:
                self.out.append(self.acc)
                if self.acc == 0xFF:          # byte stuffing
                    self.out.append(0x00)
                self.acc = 0
                self.n = 0

    def flush(self):
        while self.n:
            self.write(1, 1)                  # pad with 1s
        return bytes(self.out)


def _fdct(block):
    """Separable float DCT-II on an 8x8 block already level-shifted by -128."""
    tmp = [0.0] * 64
    for y in range(8):
        row = block[y * 8:y * 8 + 8]
        for u in range(8):
            cu = _C[u]
            s = 0.0
            for x in range(8):
                s += row[x] * _COS[x][u]
            tmp[y * 8 + u] = 0.5 * cu * s
    out = [0.0] * 64
    for u in range(8):
        col = [tmp[y * 8 + u] for y in range(8)]
        for v in range(8):
            cv = _C[v]
            s = 0.0
            for y in range(8):
                s += col[y] * _COS[y][v]
            out[v * 8 + u] = 0.5 * cv * s
    return out


def _encode_block(bw, block, prev_dc):
    coeffs = _fdct(block)
    q = [int(round(coeffs[ZIGZAG[i]] / QUANT_LUMA[ZIGZAG[i]])) for i in range(64)]

    diff = q[0] - prev_dc
    size, pattern = _magnitude(diff)
    code, length = _DC_CODES[size]
    bw.write(code, length)
    if size:
        bw.write(pattern, size)

    run = 0
    for k in range(1, 64):
        if q[k] == 0:
            run += 1
            continue
        while run > 15:                        # ZRL
            code, length = _AC_CODES[0xF0]
            bw.write(code, length)
            run -= 16
        size, pattern = _magnitude(q[k])
        code, length = _AC_CODES[(run << 4) | size]
        bw.write(code, length)
        bw.write(pattern, size)
        run = 0
    if run:                                    # EOB
        code, length = _AC_CODES[0x00]
        bw.write(code, length)

    return q[0]


def _segment(marker, payload):
    return bytes([0xFF, marker]) + struct.pack(">H", len(payload) + 2) + payload


def encode(width, height, rgb, quality_quant=None):
    """Encode 8-bit RGB (w*h*3 bytes) as a baseline JPEG. Returns bytes."""
    if len(rgb) != width * height * 3:
        raise ValueError("rgb buffer size does not match dimensions")
    if width % 8 or height % 8:
        raise ValueError("dimensions must be multiples of 8 (4:4:4, no padding)")

    # --- RGB -> YCbCr planes (JFIF full range) ---
    n = width * height
    Y = [0.0] * n
    Cb = [0.0] * n
    Cr = [0.0] * n
    for i in range(n):
        r, g, b = rgb[3 * i], rgb[3 * i + 1], rgb[3 * i + 2]
        Y[i] = 0.299 * r + 0.587 * g + 0.114 * b
        Cb[i] = -0.168736 * r - 0.331264 * g + 0.5 * b + 128.0
        Cr[i] = 0.5 * r - 0.418688 * g - 0.081312 * b + 128.0

    quant = bytes(QUANT_LUMA[ZIGZAG[i]] for i in range(64))
    dqt = _segment(0xDB, bytes([0x00]) + quant)
    sof0 = _segment(0xC0, struct.pack(
        ">BHHB", 8, height, width, 3)
        + bytes([1, 0x11, 0, 2, 0x11, 0, 3, 0x11, 0]))
    dht = (_segment(0xC4, bytes([0x00]) + bytes(DC_BITS) + bytes(DC_VALS))
           + _segment(0xC4, bytes([0x10]) + bytes(AC_BITS) + bytes(AC_VALS)))
    sos = _segment(0xDA, bytes([3, 1, 0x00, 2, 0x00, 3, 0x00, 0, 63, 0]))

    bw = _BitWriter()
    prev = [0, 0, 0]
    for by in range(height // 8):
        for bx in range(width // 8):
            for c, plane in enumerate((Y, Cb, Cr)):
                block = []
                for y in range(8):
                    row = (by * 8 + y) * width + bx * 8
                    for x in range(8):
                        block.append(plane[row + x] - 128.0)
                prev[c] = _encode_block(bw, block, prev[c])

    return b"\xff\xd8" + dqt + sof0 + dht + sos + bw.flush() + b"\xff\xd9"

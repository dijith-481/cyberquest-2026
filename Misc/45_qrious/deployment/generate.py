#!/usr/bin/env python3
"""QRious — seeded generator for Misc slot 45.

Builds 14 same-size black/white QR-like PNGs (IMG_001.png ... IMG_014.png).

Construction:
  * Flag is encoded as a real Version-3, EC-M QR matrix T (29x29 modules,
    mask 0), rendered with a 4-module quiet zone and SCALE x upscaling.
  * Four random data masks A,B,C,D are drawn; E = T ^ A ^ B ^ C ^ D over
    the data modules. All function modules (finders, separators, timing,
    alignment, format, dark module) are copied verbatim from T into every
    share, so each share looks QR-ish but carries random data.
  * Nine decoy shares carry random data with the same function pattern.
  * The 5 true shares are placed at 5 random positions among the 14 files.

Uniqueness gate (the important part):
  * Every non-empty subset (2^14 - 1 = 16383) is XORed at module level and
    run through a real RS-syndrome + header decode attempt. The generator
    refuses to write output unless exactly one subset decodes: the true one.
  * On collision it discards everything and retries with the next attempt
    counter (deterministic per seed).

Stdlib only: QR encoder, Reed-Solomon codec, PNG writer, and the decode
check are all vendored below. No Pillow / OpenCV / zbar needed to build.

Usage:
    python3 deployment/generate.py --seed 45 --flag 'cyber_quest{...}' --out handout
"""

import argparse
import hashlib
import itertools
import random
import struct
import sys
import zlib
from pathlib import Path

# --------------------------------------------------------------------------
# QR constants: Version 3, EC level M, mask 0
# --------------------------------------------------------------------------

VERSION = 3
SIZE = 4 * VERSION + 17          # 29
EC_LEVEL_BITS = 0b00             # M (spec: L=01 M=00 Q=11 H=10)
MASK = 0
N_DATA_CW = 44
N_ECC_CW = 26
N_TOTAL_CW = N_DATA_CW + N_ECC_CW  # 70, single block
QUIET = 4
SCALE = 8

ALIGN_CENTERS = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26]}[VERSION]

# --------------------------------------------------------------------------
# GF(256) with poly 0x11D
# --------------------------------------------------------------------------

_GF_EXP = [0] * 512
_GF_LOG = [0] * 256


def _gf_init():
    x = 1
    for i in range(255):
        _GF_EXP[i] = x
        _GF_LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        _GF_EXP[i] = _GF_EXP[i - 255]


_gf_init()


def _gf_mul(a, b):
    if a == 0 or b == 0:
        return 0
    return _GF_EXP[_GF_LOG[a] + _GF_LOG[b]]


def _rs_generator(deg):
    poly = [1]
    for i in range(deg):
        nxt = [0] * (len(poly) + 1)
        for j, c in enumerate(poly):
            nxt[j] ^= _gf_mul(c, _GF_EXP[i])
            nxt[j + 1] ^= c
        poly = nxt
    return poly  # len deg+1, poly[0..deg]


_RS_GEN = _rs_generator(N_ECC_CW)


def rs_encode_clean(data):
    """Straightforward polynomial-division RS encode (highest-first)."""
    assert len(data) == N_DATA_CW
    gen = list(reversed(_RS_GEN))  # highest-first, gen[0] == 1
    assert gen[0] == 1
    msg = list(data) + [0] * N_ECC_CW
    for i in range(N_DATA_CW):
        coef = msg[i]
        if coef:
            for j in range(len(gen)):
                msg[i + j] ^= _gf_mul(gen[j], coef)
    return msg[N_DATA_CW:]


def rs_syndromes(codewords):
    """Return list of N_ECC_CW syndromes (0 == valid)."""
    assert len(codewords) == N_TOTAL_CW
    out = []
    for i in range(N_ECC_CW):
        acc = 0
        for c in codewords:
            acc = _gf_mul(acc, _GF_EXP[i]) ^ c
        out.append(acc)
    return out


# --------------------------------------------------------------------------
# Data encoding (byte mode, versions 1-9 => 8-bit count)
# --------------------------------------------------------------------------

def encode_data_codewords(payload: bytes):
    if len(payload) > N_DATA_CW - 2:
        raise ValueError(f"payload too long for V{VERSION}-M ({len(payload)} bytes)")
    bits = []
    # mode 0100
    bits += [0, 1, 0, 0]
    # char count 8 bits
    for i in range(7, -1, -1):
        bits.append((len(payload) >> i) & 1)
    for b in payload:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    # terminator up to 4 zeros
    cap = N_DATA_CW * 8
    bits += [0] * min(4, cap - len(bits))
    # pad to byte
    while len(bits) % 8:
        bits.append(0)
    # bytes
    cw = []
    for i in range(0, len(bits), 8):
        v = 0
        for b in bits[i:i + 8]:
            v = (v << 1) | b
        cw.append(v)
    # pad bytes EC 11
    pads = [0xEC, 0x11]
    k = 0
    while len(cw) < N_DATA_CW:
        cw.append(pads[k % 2])
        k += 1
    return cw


# --------------------------------------------------------------------------
# Matrix construction
# --------------------------------------------------------------------------

def _finder(m, is_func, r, c):
    pat = [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1],
    ]
    for dr in range(7):
        for dc in range(7):
            m[r + dr][c + dc] = pat[dr][dc]
            is_func[r + dr][c + dc] = True
    # separators (white ring)
    for dc in range(-1, 8):
        for dr in (-1, 7):
            rr, cc = r + dr, c + dc
            if 0 <= rr < SIZE and 0 <= cc < SIZE and not is_func[rr][cc]:
                m[rr][cc] = 0
                is_func[rr][cc] = True
    for dr in range(-1, 8):
        for dc in (-1, 7):
            rr, cc = r + dr, c + dc
            if 0 <= rr < SIZE and 0 <= cc < SIZE and not is_func[rr][cc]:
                m[rr][cc] = 0
                is_func[rr][cc] = True


def build_function_mask():
    m = [[0] * SIZE for _ in range(SIZE)]
    is_func = [[False] * SIZE for _ in range(SIZE)]
    _finder(m, is_func, 0, 0)
    _finder(m, is_func, 0, SIZE - 7)
    _finder(m, is_func, SIZE - 7, 0)
    # timing
    for i in range(8, SIZE - 8):
        m[6][i] = 1 if i % 2 == 0 else 0
        is_func[6][i] = True
        m[i][6] = 1 if i % 2 == 0 else 0
        is_func[i][6] = True
    # alignment (V3: single at (22,22))
    for centers in itertools.product(ALIGN_CENTERS, repeat=2):
        cr, cc = centers[1], centers[0]
        # skip overlaps with finders
        if (cr < 9 and cc < 9) or (cr < 9 and cc > SIZE - 10) or (cr > SIZE - 10 and cc < 9):
            continue
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                v = 1 if max(abs(dr), abs(dc)) != 1 else 0
                m[cr + dr][cc + dc] = v
                is_func[cr + dr][cc + dc] = True
    # format info positions + dark module reserved
    for i in range(9):
        if i != 6:
            is_func[8][i] = True
            is_func[i][8] = True
    for i in range(8):
        is_func[SIZE - 1 - i][8] = True
        is_func[8][SIZE - 1 - i] = True
    is_func[SIZE - 7 - 1 + 1][8] = True  # dark module (21,8) covered below anyway
    return m, is_func


def format_bits(ec_bits, mask):
    data = (ec_bits << 3) | mask  # 5 bits
    v = data << 10
    g = 0b10100110111
    for i in range(14, 9, -1):
        if (v >> i) & 1:
            v ^= g << (i - 10)
    rem = v & 0x3FF
    bits = ((data << 10) | rem) ^ 0b101010000010010
    return bits  # 15 bits, bit14 = MSB


def place_format(m, is_func, bits):
    # bits: bit14 first. Canonical placement per the QR spec.
    def bit(k):
        return (bits >> k) & 1
    seq = [(14 - i) for i in range(15)]  # MSB..LSB
    # positions for copy 1 (around top-left finder)
    pos1 = [(8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8),
            (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8)]
    for (r, c), k in zip(pos1, seq):
        m[r][c] = bit(k)
    # positions for copy 2 (split)
    pos2 = [(SIZE - 1, 8), (SIZE - 2, 8), (SIZE - 3, 8), (SIZE - 4, 8),
            (SIZE - 5, 8), (SIZE - 6, 8), (SIZE - 7, 8),
            (8, SIZE - 8), (8, SIZE - 7), (8, SIZE - 6), (8, SIZE - 5),
            (8, SIZE - 4), (8, SIZE - 3), (8, SIZE - 2), (8, SIZE - 1)]
    for (r, c), k in zip(pos2, seq):
        m[r][c] = bit(k)
    # dark module always black
    m[4 * VERSION + 9][8] = 1


def mask_bit(mask, r, c):
    if mask == 0:
        return (r + c) % 2 == 0
    raise ValueError("only mask 0 supported")


def data_positions(is_func):
    """Yield (r,c) in QR data-placement order (excluding function modules)."""
    pos = []
    col = SIZE - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        for i in range(SIZE):
            r = SIZE - 1 - i if upward else i
            for dc in (0, 1):
                cc = col - dc
                if not is_func[r][cc]:
                    pos.append((r, cc))
        upward = not upward
        col -= 2
    return pos


def build_matrix(payload: bytes):
    data_cw = encode_data_codewords(payload)
    ecc = rs_encode_clean(data_cw)
    full = data_cw + ecc
    assert len(full) == N_TOTAL_CW
    # bit stream MSB first
    bits = []
    for cw in full:
        for i in range(7, -1, -1):
            bits.append((cw >> i) & 1)
    base, is_func = build_function_mask()
    m = [row[:] for row in base]
    pos_full = data_positions(is_func)
    # Version 3 carries 7 remainder modules: the last slots in placement
    # order stay light and are function, not data.
    assert len(pos_full) == N_TOTAL_CW * 8 + 7, len(pos_full)
    pos = pos_full[:N_TOTAL_CW * 8]
    for (r, c) in pos_full[N_TOTAL_CW * 8:]:
        is_func[r][c] = True
        m[r][c] = 0
    for (r, c), b in zip(pos, bits):
        if mask_bit(MASK, r, c):
            b ^= 1
        m[r][c] = b
    fb = format_bits(EC_LEVEL_BITS, MASK)
    place_format(m, is_func, fb)
    # mark format cells func (already) and dark module
    is_func[4 * VERSION + 9][8] = True
    return m, is_func, full, data_cw


# Fast 256x256 multiply table for the gate (early-exit syndromes).
_MUL_TAB = [[0] * 256 for _ in range(256)]
for _a in range(256):
    for _b in range(256):
        if _a and _b:
            _MUL_TAB[_a][_b] = _GF_EXP[_GF_LOG[_a] + _GF_LOG[_b]]
_MUL = _MUL_TAB


def _syndromes_zero_early(cw):
    """True iff all 26 syndromes are zero. Early-exits on the first failure
    (random data almost always fails syndrome 0)."""
    row = _MUL
    for i in range(N_ECC_CW):
        a = _GF_EXP[i]
        acc = 0
        for c in cw:
            acc = row[acc][a] ^ c
        if acc:
            return False
    return True


# --------------------------------------------------------------------------
# Decode attempt (the uniqueness gate): RS syndrome + header sanity
# --------------------------------------------------------------------------

def extract_codewords(modules, is_func, pos):
    raw = []
    for (r, c) in pos:
        b = modules[r][c]
        if mask_bit(MASK, r, c):
            b ^= 1
        raw.append(b)
    cw = []
    for i in range(0, len(raw), 8):
        v = 0
        for b in raw[i:i + 8]:
            v = (v << 1) | b
        cw.append(v)
    return cw


def try_decode_modules(modules, is_func, pos):
    """Return payload bytes if modules form a valid V3-M QR, else None.

    Checks: RS syndromes all zero, mode == 0100 (byte), count sane,
    terminator / padding consistent enough to be a real decode.
    """
    # finder sanity: the three 7x7 finders must match the true pattern,
    # otherwise no real-world decoder would even locate the symbol.
    for (fr, fc) in ((0, 0), (0, SIZE - 7), (SIZE - 7, 0)):
        pat = [
            [1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 1, 0, 1],
            [1, 0, 1, 1, 1, 0, 1],
            [1, 0, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1],
        ]
        for dr in range(7):
            for dc in range(7):
                if modules[fr + dr][fc + dc] != pat[dr][dc]:
                    return None
    cw = extract_codewords(modules, is_func, pos)
    if len(cw) != N_TOTAL_CW:
        return None
    if any(rs_syndromes(cw)):
        return None
    # parse byte-mode header
    bits = []
    for w in cw[:N_DATA_CW]:
        for i in range(7, -1, -1):
            bits.append((w >> i) & 1)
    mode = (bits[0] << 3) | (bits[1] << 2) | (bits[2] << 1) | bits[3]
    if mode != 0b0100:
        return None
    count = 0
    for b in bits[4:12]:
        count = (count << 1) | b
    if count > N_DATA_CW - 2 or count <= 0:
        return None
    total = 12 + count * 8
    if total > len(bits):
        return None
    payload = bytearray()
    for i in range(count):
        v = 0
        for b in bits[12 + i * 8:12 + (i + 1) * 8]:
            v = (v << 1) | b
        payload.append(v)
    return bytes(payload)


# --------------------------------------------------------------------------
# PNG (stdlib): 8-bit grayscale, filter 0
# --------------------------------------------------------------------------

def write_png_gray(path, pixels, w, h):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(pixels[y * w:(y + 1) * w])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", comp) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


def read_png_gray(path):
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    off = 8
    w = h = None
    bitd = ctyp = None
    idat = bytearray()
    while off < len(data):
        (ln,) = struct.unpack(">I", data[off:off + 4])
        typ = data[off + 4:off + 8]
        body = data[off + 8:off + 8 + ln]
        if typ == b"IHDR":
            w, h, bitd, ctyp, comp, filt, inter = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        off += 12 + ln
    assert bitd == 8 and ctyp == 0, f"unexpected PNG type {bitd}/{ctyp}"
    raw = zlib.decompress(bytes(idat))
    px = bytearray(w * h)
    stride = w + 1
    prev = bytearray(w)
    for y in range(h):
        f = raw[y * stride]
        cur = bytearray(raw[y * stride + 1:(y + 1) * stride])
        if f == 1:
            for i in range(1, w):
                cur[i] = (cur[i] + cur[i - 1]) & 0xFF
        elif f == 2:
            for i in range(w):
                cur[i] = (cur[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(w):
                a = cur[i - 1] if i else 0
                cur[i] = (cur[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(w):
                a = cur[i - 1] if i else 0
                b = prev[i]
                c = prev[i - 1] if i else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[i] = (cur[i] + pr) & 0xFF
        elif f != 0:
            raise ValueError(f"bad filter {f}")
        px[y * w:(y + 1) * w] = cur
        prev = cur
    return px, w, h


# --------------------------------------------------------------------------
# Share construction + exhaustive gate
# --------------------------------------------------------------------------

N_FILES = 14
N_TRUE = 5


def xor_modules(grids):
    n = len(grids[0])
    out = [0] * n
    for g in grids:
        for i, b in enumerate(g):
            out[i] ^= b
    return out


def _flat_to_codewords(flat, pos):
    """Extract the 70 codewords from a flat SIZE*SIZE grid (mask 0)."""
    cw = [0] * N_TOTAL_CW
    for k in range(N_TOTAL_CW):
        v = 0
        base = k * 8
        for j in range(8):
            r, c = pos[base + j]
            b = flat[r * SIZE + c] ^ (1 if (r + c) % 2 == 0 else 0)
            v = (v << 1) | b
        cw[k] = v
    return cw


def _payload_from_codewords(cw):
    bits = []
    for w in cw[:N_DATA_CW]:
        for i in range(7, -1, -1):
            bits.append((w >> i) & 1)
    mode = (bits[0] << 3) | (bits[1] << 2) | (bits[2] << 1) | bits[3]
    if mode != 0b0100:
        return None
    count = 0
    for b in bits[4:12]:
        count = (count << 1) | b
    if count > N_DATA_CW - 2 or count <= 0:
        return None
    out = bytearray()
    for i in range(count):
        v = 0
        for b in bits[12 + i * 8:12 + (i + 1) * 8]:
            v = (v << 1) | b
        out.append(v)
    return bytes(out)


def build_attempt(flag_bytes, rng):
    T, is_func, full, data_cw = build_matrix(flag_bytes)
    pos = data_positions(is_func)
    flat_T = [T[r][c] for r in range(SIZE) for c in range(SIZE)]
    func_idx = [is_func[r][c] for r in range(SIZE) for c in range(SIZE)]
    data_idx = [i for i, f in enumerate(func_idx) if not f]

    # random pads over data modules only
    pads = []
    for _ in range(N_TRUE - 1):
        pads.append([rng.getrandbits(1) for _ in data_idx])
    # E over data modules
    t_data = [flat_T[i] for i in data_idx]
    e_data = list(t_data)
    for p in pads:
        for i, b in enumerate(p):
            e_data[i] ^= b
    true_datas = pads + [e_data]

    # decoys
    decoy_datas = [[rng.getrandbits(1) for _ in data_idx]
                   for _ in range(N_FILES - N_TRUE)]

    # assemble full grids: function bits from T, data bits from above
    def assemble(d):
        g = list(flat_T)
        for idx, b in zip(data_idx, d):
            g[idx] = b
        return g

    true_grids = [assemble(d) for d in true_datas]
    decoy_grids = [assemble(d) for d in decoy_datas]

    all_grids = true_grids + decoy_grids
    order = list(range(N_FILES))
    rng.shuffle(order)
    # order[k] = old position now at file k; invert to find true files
    shuffled = [None] * N_FILES
    is_true = [False] * N_FILES
    for new_pos, old_pos in enumerate(order):
        if old_pos < N_TRUE:
            shuffled[new_pos] = true_grids[old_pos]
            is_true[new_pos] = True
        else:
            shuffled[new_pos] = decoy_grids[old_pos - N_TRUE]
    true_set = frozenset(i for i, t in enumerate(is_true) if t)

    # ---- exhaustive gate, codeword-level (linear: extract(XOR) = XOR extract)
    # Even-sized subsets always fail the finder check: every share carries
    # identical function modules, so an even XOR clears all black function
    # cells (finders included) and no locator stage can lock on. We assert
    # this once on the matrix level and then only RS-test odd subsets.
    def to_matrix(flat):
        return [flat[r * SIZE:(r + 1) * SIZE] for r in range(SIZE)]

    # one matrix-level proof that an even subset breaks the finders
    _even_demo = [a ^ b for a, b in zip(shuffled[0], shuffled[1])] \
        if N_FILES >= 2 else None
    if _even_demo is not None:
        _m = to_matrix(_even_demo)
        assert try_decode_modules(_m, is_func, pos) is None

    share_cw = [_flat_to_codewords(g, pos) for g in shuffled]
    # parity: odd subsets keep the function pattern, even ones clear it
    decodable = []
    # Gray-code-free direct enumeration over odd masks only (8191 for N=14).
    for mask in range(1, 1 << N_FILES):
        if bin(mask).count("1") % 2 == 0:
            continue
        x = [0] * N_TOTAL_CW
        mm = mask
        si = 0
        while mm:
            if mm & 1:
                sc = share_cw[si]
                for j in range(N_TOTAL_CW):
                    x[j] ^= sc[j]
            si += 1
            mm >>= 1
        if not _syndromes_zero_early(x):
            continue
        payload = _payload_from_codewords(x)
        if payload is not None:
            idxs = frozenset(i for i in range(N_FILES) if mask & (1 << i))
            decodable.append((idxs, payload))
    return {
        "T": T, "is_func": is_func, "pos": pos, "full": full,
        "grids": shuffled, "true_set": true_set, "decodable": decodable,
    }


def render_with_quiet_scale(flat):
    W = SIZE + 2 * QUIET
    px_w = W * SCALE
    px = bytearray(px_w * px_w)
    for r in range(W):
        for c in range(W):
            if QUIET <= r < QUIET + SIZE and QUIET <= c < QUIET + SIZE:
                b = flat[(r - QUIET) * SIZE + (c - QUIET)]
            else:
                b = 0
            v = 0 if b else 255
            for dy in range(SCALE):
                base = ((r * SCALE + dy) * px_w) + c * SCALE
                for dx in range(SCALE):
                    px[base + dx] = v
    return px, px_w, px_w


def generate(seed, flag, outdir):
    flag_bytes = flag.encode()
    # sanity: must fit V3-M byte mode
    encode_data_codewords(flag_bytes)
    attempt = 0
    while True:
        rng = random.Random(f"{seed}|{flag}|attempt={attempt}")
        res = build_attempt(flag_bytes, rng)
        dec = res["decodable"]
        if len(dec) == 1 and dec[0][0] == res["true_set"]:
            try:
                payload = dec[0][1].decode()
            except UnicodeDecodeError:
                payload = None
            if payload == flag:
                break
        attempt += 1
        if attempt > 200:
            raise RuntimeError("could not find collision-free split in 200 attempts")
        continue
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for i, g in enumerate(res["grids"]):
        px, w, h = render_with_quiet_scale(g)
        write_png_gray(outdir / f"IMG_{i + 1:03d}.png", px, w, h)
    # provenance (no answers: only hashes + true-set hash commitment)
    commit = hashlib.sha256(
        ",".join(sorted(str(i) for i in res["true_set"])).encode()).hexdigest()[:16]
    return {"attempt": attempt, "true_set": sorted(res["true_set"]), "commit": commit}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--flag", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    info = generate(args.seed, args.flag, args.out)
    print(f"wrote {N_FILES} PNGs to {args.out} (attempt {info['attempt']}, "
          f"true={info['true_set']}, commit={info['commit']})")


if __name__ == "__main__":
    main()

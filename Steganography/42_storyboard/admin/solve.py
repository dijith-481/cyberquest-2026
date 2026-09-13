#!/usr/bin/env python3
"""42_storyboard — reference solver (stdlib + ffmpeg only).

1. Decode thumbnails, diff consecutive frames: 28 huge spikes -> 29 scenes.
   The first two frames of every scene are near-identical (the twin takes).
2. Decode full frames. Crop the 116x64 ASCII grid, binarize each cell
   (ink vs background) into a 35-bit mask. No font knowledge needed.
   The video codec blurs a few pixels per cell, so masks are compared by
   Hamming distance: twin glyphs differ in >=13 bits, codec noise in a few.
3. The swapping masks reveal 5 twin pairs ({@,M}, {%,W}, ...). Either frame
   alone looks random.
4. Per scene, per vertical band (4 ascii cols = 1 QR module): fraction of
   cells whose mask changed well past the noise floor. One QR row per scene.
5. Unmask (mask 0), read the Version-3 codewords, check the Reed-Solomon
   parity, parse byte mode -> flag. (Add a 4-module quiet zone if you want
   to scan the bitmap with a phone instead.)
"""
import subprocess
import sys

COLS, ROWS = 116, 64
CELL_W, CELL_H = 6, 8
GLYPH_W, GLYPH_H = 5, 7
GOX, GOY = 0, 0
ML, MT = 8, 20
FW, FH = 712, 550
QR_N = 29
BAND_W = COLS // QR_N  # 4
N_SCENES = 29
THRESH = 40
HAMM_T = 5  # twin masks differ by >=13 bits; codec noise flips a few


def decode_all(path, vf, pix_fmt, w, h):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", vf,
           "-f", "rawvideo", "-pix_fmt", pix_fmt, "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    raw = p.stdout.read()
    p.wait()
    assert len(raw) % (w * h * (3 if pix_fmt == "rgb24" else 1)) == 0, "truncated decode"
    fs = w * h * (3 if pix_fmt == "rgb24" else 1)
    return [raw[i * fs:(i + 1) * fs] for i in range(len(raw) // fs)]


def find_scenes(thumbs):
    diffs = []
    for i in range(1, len(thumbs)):
        a, b = thumbs[i - 1], thumbs[i]
        diffs.append(sum(abs(x - y) for x, y in zip(a, b)) / len(a))
    order = sorted(range(len(diffs)), key=lambda i: -diffs[i])
    cuts = sorted(order[:N_SCENES - 1])
    return [0] + [c + 1 for c in cuts], diffs


def cell_mask(frame, cx, cy):
    m = 0
    bit = 0
    for r in range(GLYPH_H):
        for c in range(GLYPH_W):
            xx = ML + cx * CELL_W + GOX + c
            yy = MT + cy * CELL_H + GOY + r
            o = (yy * FW + xx) * 3
            if max(frame[o], frame[o + 1], frame[o + 2]) > THRESH:
                m |= (1 << bit)
            bit += 1
    return m


# ---------------- QR Version 3 helpers (function map + RS check) ----------------
EXP = [0] * 512
LOG = [0] * 256
_x = 1
for _i in range(255):
    EXP[_i] = _x
    LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    EXP[_i] = EXP[_i - 255]


def gf_mul(a, b):
    return 0 if a == 0 or b == 0 else EXP[LOG[a] + LOG[b]]


def rs_remainder(data, nsym):
    gen = [1]
    for i in range(nsym):
        ng = [0] * (len(gen) + 1)
        for j in range(len(gen)):
            ng[j] ^= gf_mul(gen[j], EXP[i])
            ng[j + 1] ^= gen[j]
        gen = ng
    gen = gen[::-1]
    out = list(data) + [0] * nsym
    for i in range(len(data)):
        coef = out[i]
        if coef:
            for j in range(len(gen)):
                out[i + j] ^= gf_mul(gen[j], coef)
    return out[len(data):]


def func_map():
    n = QR_N
    func = [[False] * n for _ in range(n)]

    def finder(r, c):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                rr, cc = r + dr, c + dc
                if 0 <= rr < n and 0 <= cc < n:
                    func[rr][cc] = True

    finder(0, 0)
    finder(0, n - 7)
    finder(n - 7, 0)
    for i in range(8, n - 8):
        func[6][i] = func[i][6] = True
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            func[22 + dr][22 + dc] = True
    func[4 * 3 + 9][8] = True
    for i in range(6):
        func[8][i] = True
    func[8][7] = func[8][8] = func[7][8] = True
    for i in range(6):
        func[5 - i][8] = True
    for i in range(8):
        func[8][n - 1 - i] = True
    for i in range(7):
        func[n - 1 - i][8] = True
    return func


def data_positions(func):
    n = QR_N
    pos = []
    col = n - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        for i in range(n):
            r = n - 1 - i if upward else i
            for c in (col, col - 1):
                if not func[r][c]:
                    pos.append((r, c))
        upward = not upward
        col -= 2
    return pos


def main(path):
    thumbs = decode_all(path, "scale=120:114,format=gray", "gray", 120, 114)
    starts, diffs = find_scenes(thumbs)
    order = sorted(range(len(diffs)), key=lambda i: -diffs[i])
    print(f"frames: {len(thumbs)}", file=sys.stderr)
    print(f"top transitions: {[(i + 1, round(diffs[i], 2)) for i in order[:5]]}", file=sys.stderr)
    print(f"scene starts: {starts}", file=sys.stderr)
    assert len(starts) == N_SCENES, f"want {N_SCENES} scenes, got {len(starts)}"

    full = decode_all(path, "format=rgb24", "rgb24", FW, FH)
    assert len(full) == len(thumbs)

    rows = []
    for s in range(N_SCENES):
        A, B = full[starts[s]], full[starts[s] + 1]
        bits = []
        for band in range(QR_N):
            ch = to = 0
            for cx in range(band * BAND_W, (band + 1) * BAND_W):
                for cy in range(ROWS):
                    to += 1
                    ma, mb = cell_mask(A, cx, cy), cell_mask(B, cx, cy)
                    if bin(ma ^ mb).count("1") > HAMM_T:
                        ch += 1
            f = ch / to
            assert f < 0.35 or f > 0.65, f"scene {s} band {band}: frac {f:.3f}"
            bits.append(1 if f > 0.5 else 0)
        rows.append(bits)

    m = [[rows[r][c] ^ (1 if (r + c) % 2 == 0 else 0) for c in range(QR_N)] for r in range(QR_N)]
    print("QR bitmap:", file=sys.stderr)
    for row in m:
        print(''.join('##' if v else '  ' for v in row), file=sys.stderr)

    pos = data_positions(func_map())
    allbits = [m[r][c] for (r, c) in pos][:(44 + 26) * 8]
    cw = [int(''.join(map(str, allbits[i:i + 8])), 2) for i in range(0, len(allbits), 8)]
    assert rs_remainder(cw[:44], 26) == cw[44:], "RS parity mismatch"
    bits = []
    for w in cw[:44]:
        bits += [(w >> i) & 1 for i in range(7, -1, -1)]
    assert int(''.join(map(str, bits[:4])), 2) == 4, "not byte mode"
    ln = int(''.join(map(str, bits[4:12])), 2)
    flag = bytes(int(''.join(map(str, bits[12 + k * 8:12 + k * 8 + 8])), 2) for k in range(ln))
    print(flag.decode())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "storyboard.mkv")

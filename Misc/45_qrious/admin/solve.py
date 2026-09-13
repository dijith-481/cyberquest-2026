#!/usr/bin/env python3
"""QRious — reference solver (stdlib only).

Brute-forces all 2^14 - 1 = 16383 non-empty subsets: XOR the selected
images pixel-by-pixel (equivalently module-by-module) and attempt a real
QR decode (finder check + Reed-Solomon syndromes + byte-mode header).

Usage:
    python3 admin/solve.py handout
    python3 admin/solve.py handout/IMG_001.png ... IMG_014.png
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "deployment"))
from generate import (  # noqa: E402
    N_ECC_CW,
    N_TOTAL_CW,
    QUIET,
    SIZE,
    _MUL,
    _payload_from_codewords,
    _syndromes_zero_early,
    build_function_mask,
    data_positions,
    read_png_gray,
)


def load_modules(path):
    px, w, h = read_png_gray(path)
    assert w == h, f"{path}: not square ({w}x{h})"
    assert set(bytes(px)) <= {0, 255}, f"{path}: not pure black/white"
    grid = SIZE + 2 * QUIET
    assert w % grid == 0, f"{path}: size {w} not a multiple of {grid}"
    scale = w // grid
    mods = []
    for r in range(grid):
        for c in range(grid):
            v = px[(r * scale + scale // 2) * w + (c * scale + scale // 2)]
            mods.append(1 if v < 128 else 0)
    # quiet zone must be all white
    for r in range(grid):
        for c in range(grid):
            if r < QUIET or r >= QUIET + SIZE or c < QUIET or c >= QUIET + SIZE:
                assert mods[r * grid + c] == 0, f"{path}: quiet zone not white"
    core = []
    for r in range(SIZE):
        for c in range(SIZE):
            core.append(mods[(r + QUIET) * grid + (c + QUIET)])
    return core


def modules_to_codewords(flat, pos):
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


def main():
    args = sys.argv[1:]
    if len(args) == 1 and Path(args[0]).is_dir():
        files = sorted(Path(args[0]).glob("*.png"))
    else:
        files = [Path(a) for a in args]
    assert len(files) == 14, f"expected 14 PNGs, got {len(files)}"
    print(f"loaded {len(files)} images")
    grids = [load_modules(str(f)) for f in files]

    _, is_func = build_function_mask()
    # remainder modules (last 7 in placement order) are function, not data
    pos_full = data_positions(is_func)
    for (r, c) in pos_full[N_TOTAL_CW * 8:]:
        is_func[r][c] = True
    pos = pos_full[:N_TOTAL_CW * 8]

    share_cw = [modules_to_codewords(g, pos) for g in grids]
    n = len(files)
    hits = []
    for mask in range(1, 1 << n):
        if bin(mask).count("1") % 2 == 0:
            continue  # even XOR clears the finders; no locator can lock on
        x = [0] * N_TOTAL_CW
        for si in range(n):
            if mask & (1 << si):
                sc = share_cw[si]
                for j in range(N_TOTAL_CW):
                    x[j] ^= sc[j]
        if not _syndromes_zero_early(x):
            continue
        payload = _payload_from_codewords(x)
        if payload is not None:
            idxs = [si + 1 for si in range(n) if mask & (1 << si)]
            hits.append((idxs, payload))
    print(f"decodable subsets: {len(hits)}")
    for idxs, payload in hits:
        try:
            text = payload.decode()
        except UnicodeDecodeError:
            text = repr(payload)
        print(f"  files {idxs} -> {text}")
    if len(hits) == 1:
        print(hits[0][1].decode(errors='replace'))
    return 0 if len(hits) == 1 else 1


if __name__ == "__main__":
    sys.exit(main())

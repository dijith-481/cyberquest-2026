#!/usr/bin/env python3
"""fine_print — reference solver.

Reimplements `strings` in pure Python (runs of printable ASCII >= 4),
keeps the lines at the tell length, XORs them byte-by-byte.

    python3 admin/solve.py [handout_dir|binary]
"""

import os
import re
import sys

TELL_LEN = len("cyber_quest{x0r_a11_th3_str1ngs_2gether_3f8a1d}")


def strings(path: str):
    with open(path, "rb") as f:
        data = f.read()
    return re.findall(rb"[\x20-\x7e]{4,}", data)


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "handout"
    binary = target if os.path.isfile(target) else os.path.join(target, "licenseguard")
    cands = [s for s in strings(binary) if len(s) == TELL_LEN]
    if len(cands) < 4:
        raise SystemExit(
            f"expected >= 4 tell-length ({TELL_LEN}) strings, found {len(cands)}"
        )
    # The four fragments are the tell; extra length-collisions (there are
    # none in the shipped binary) would only add noise, so take the first 4
    # in file order — matching `strings` output order.
    cands = cands[:4]
    flag = bytearray(TELL_LEN)
    for c in cands:
        for i in range(TELL_LEN):
            flag[i] ^= c[i]
    print(bytes(flag).decode())


if __name__ == "__main__":
    main()

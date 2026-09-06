#!/usr/bin/env python3
"""two_time_pad — scripted solve.

  1. Confirm the pad is reused: XOR of two sealed memos cancels the
     identical header lines instead of looking like noise.
  2. Recover the pad: the draft shelf copy of memo 0049 is the plaintext
     of a sealed memo, so sealed_0049 XOR draft_0049 is the pad itself —
     for the draft's full length, which covers every memo in the cabinet.
  3. XOR every sealed memo against the recovered pad and read them.

Usage:
    python3 solve.py [HANDOUT_DIR]     # default: ../handout
"""

import os
import sys

HANDOUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "handout")
MEMOS = os.path.join(HANDOUT, "memos")


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def main() -> int:
    c49 = read_bytes(os.path.join(MEMOS, "memo_0049.hex")).strip().decode().strip()
    c49 = bytes.fromhex(c49)
    draft = read_bytes(os.path.join(MEMOS, "memo_0049_draft.txt"))

    # -- stage 1: the pad is reused -----------------------------------------
    c51 = bytes.fromhex(read_bytes(os.path.join(MEMOS, "memo_0051.hex")).decode().strip())
    pair = xor(c49, c51)
    zeros = pair[: len("ORDINARY ENGINEERING - RECORDS DIVISION")].count(0)
    print(f"[1] XOR of two sealed memos: {zeros} zero bytes in the shared header"
          f" out of {len('ORDINARY ENGINEERING - RECORDS DIVISION')} — the pad repeats")

    # -- stage 2: recover the pad from the draft shelf ------------------------
    pad = xor(c49, draft)
    print(f"[2] pad recovered from sealed_0049 XOR draft_0049: {len(pad)} bytes")

    # -- stage 3: open the cabinet -------------------------------------------
    for mid in ("0051", "0067", "0072"):
        ct = bytes.fromhex(read_bytes(os.path.join(MEMOS, f"memo_{mid}.hex")).decode().strip())
        plain = xor(ct, pad).decode("utf-8", "replace")
        print(f"[3] memo {mid}:\n")
        print(plain)

    for line in plain.splitlines():
        if line.startswith("Flag:"):
            print("FLAG:", line.split("Flag: ", 1)[1].strip())
            return 0
    print("!! flag not found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

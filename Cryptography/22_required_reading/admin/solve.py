#!/usr/bin/env python3
"""required_reading — reference solve.

The cover memo says it plainly: each number in orientation_note.enc is
a zero-based byte offset into handbook.txt. Index, concatenate, read.

Usage:
    python3 solve.py [HANDOUT_DIR]     # default: ../handout
"""

import os
import sys

HANDOUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "handout")


def main():
    book = open(os.path.join(HANDOUT, "handbook.txt"), "rb").read()
    cipher = open(os.path.join(HANDOUT, "orientation_note.enc")).read().split()
    note = b"".join(book[int(n):int(n) + 1] for n in cipher)
    print(note.decode("ascii"))
    assert b"cyber_quest{" in note, "no flag-shaped token decoded"


if __name__ == "__main__":
    main()

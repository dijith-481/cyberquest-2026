#!/usr/bin/env python3
"""core_values — reference solve.

Simulates the documented solve path: locate the values ledger inside the
raw heap dump, keep the live (LEDJ) records whose sequence number is in
the message range, order by sequence, and read one byte per record.

    python3 admin/solve.py handout/valuesd_heap.raw
"""

import struct
import sys

TAGS = (b"LEDJ", b"AUDT")


def find_ledger(data: bytes) -> int:
    """Find the start of a run of well-formed 16-byte ledger records."""
    for off in range(0, len(data) - 16, 4):
        if data[off:off + 4] not in TAGS:
            continue
        run = 0
        o = off
        while data[o:o + 4] in TAGS:
            run += 1
            o += 16
        if run >= 40:  # the ledger is one solid block of records
            return off, run
    raise SystemExit("no ledger block found in dump")


def solve(path: str) -> str:
    data = open(path, "rb").read()
    print(f"dump: {len(data)} bytes")

    for tag_line in data.split(b"\x00"):
        if b"crash report" in tag_line:
            print("lore:", tag_line.decode()[:120], "…")
            break

    start, count = find_ledger(data)
    print(f"ledger block found at offset 0x{start:x} ({count} records)")

    live = {}
    for i in range(count):
        rec = data[start + i * 16:start + (i + 1) * 16]
        tag, seq, value = rec[0:4], struct.unpack("<I", rec[8:12])[0], rec[12]
        if tag == b"LEDJ" and 1 <= seq <= 100 and seq not in live:
            live[seq] = value  # first write wins; duplicates are none here
    print(f"live in-range LEDJ records: {len(live)}")

    flag = bytes(live[s] for s in sorted(live)).decode()
    print("flag:", flag)
    return flag


if __name__ == "__main__":
    print(solve(sys.argv[1] if len(sys.argv) > 1 else "handout/valuesd_heap.raw"))

#!/usr/bin/env python3
"""clock_skew — scripted solve.

  1. Read the door spec: standard TOTP — HMAC-SHA1, 30 s steps, 6-digit
     truncation, key = the 6-digit enrollment code as ASCII. Six digits
     of 0-9 is one million candidates.
  2. Brute-force the enrollment code against the observation log's
     (door-clock timestamp, accepted code) pairs. The door's clock being
     wrong does not matter: the log's timestamps are the door's own, so
     T = floor(door_clock / 30) is exactly what the door computed.
  3. Unseal the maintenance note (XOR against a keystream derived from
     the recovered code) and read the flag.

Usage:
    python3 solve.py [HANDOUT_DIR]     # default: ../handout
"""

import hashlib
import hmac
import os
import sys

HANDOUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "handout")


def totp(key: bytes, ts: int) -> str:
    t = ts // 30
    h = hmac.new(key, t.to_bytes(8, "big"), hashlib.sha1).digest()
    o = h[19] & 0x0F
    n = ((h[o] & 0x7F) << 24) | (h[o + 1] << 16) | (h[o + 2] << 8) | h[o + 3]
    return f"{n % 10**6:06d}"


def main() -> int:
    log = open(os.path.join(HANDOUT, "door_log.txt")).read().splitlines()
    pairs = []
    for line in log:
        if line.startswith("door-clock") and "ACCEPTED" in line:
            parts = line.split()
            pairs.append((int(parts[1]), parts[3]))
    print(f"[1] {len(pairs)} accepted codes logged at door-clock timestamps")

    # -- stage 2: recover the enrollment code --------------------------------
    first_ts, first_code = pairs[0]
    seed = None
    for n in range(10**6):
        candidate = f"{n:06d}".encode()
        if totp(candidate, first_ts) == first_code:
            if all(totp(candidate, ts) == code for ts, code in pairs[1:]):
                seed = candidate.decode()
                break
    if seed is None:
        print("!! no enrollment code matches the log")
        return 1
    print(f"[2] enrollment code recovered: {seed} (all {len(pairs)} codes confirm)")

    # -- stage 3: unseal the maintenance note --------------------------------
    blob = bytes.fromhex(open(os.path.join(HANDOUT, "maintenance_note.txt.enc")).read().strip())
    ks = bytearray()
    while len(ks) < len(blob):
        ks += hashlib.sha256(b"fac-door/seed/" + seed.encode()).digest()
    note = bytes(a ^ b for a, b in zip(blob, ks)).decode()
    print("[3] maintenance note:\n")
    print(note)

    for line in note.splitlines():
        if line.startswith("Flag:"):
            print("FLAG:", line.split("Flag: ", 1)[1].strip())
            return 0
    print("!! flag not found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

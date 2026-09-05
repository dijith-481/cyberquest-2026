#!/usr/bin/env python3
"""onion_pattern — scripted solve.

Peels handout/onion.txt by trusting each envelope's `op` field:
  hex -> base64 -> ascii85 -> mirror -> base32 -> xor-hex(p34r1)
  -> rot13 -> base64 -> xor-hex(0n10n) -> core JSON

Usage:
    python3 solve.py [HANDOUT_DIR]     # default: ../handout
"""

import base64
import codecs
import json
import os
import sys

HANDOUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "handout")


def xor_bytes(data: bytes, key: str) -> bytes:
    k = key.encode()
    return bytes(b ^ k[i % len(k)] for i, b in enumerate(data))


def peel_once(op: str, data: str, env_hint: str = "") -> str:
    if op == "hex":
        return bytes.fromhex("".join(data.split())).decode()
    if op == "base64":
        return base64.b64decode(data).decode()
    if op == "base32":
        return base64.b32decode(data).decode()
    if op == "ascii85":
        return base64.a85decode(data).decode()
    if op == "mirror":
        return data[::-1]
    if op == "rot13":
        return codecs.decode(data, "rot13")
    if op == "xor-hex":
        # the key is only ever documented in the layer's own hint
        import re
        m = re.search(r"key ([A-Za-z0-9_!@#]+)", env_hint.lower())
        if not m:
            raise ValueError("no key documented in hint")
        return xor_bytes(bytes.fromhex("".join(data.split())), m.group(1)).decode()
    raise ValueError(f"unknown op: {op}")


def main() -> int:
    blob = "".join(open(os.path.join(HANDOUT, "onion.txt")).read().split())

    # hop 0: the file itself is hex
    current = bytes.fromhex(blob).decode()
    hops = 1

    while True:
        env = json.loads(current)
        if env.get("op") is None:  # core payload
            break
        print(f"hop {hops:>2}: layer {env['layer']}/{env['of']} op={env['op']:<8} — {env['hint'][:58]}...")
        current = peel_once(env["op"], env["data"], env["hint"])
        hops += 1

    core = json.loads(current)
    print(f"\ncore reached after {hops} hops\n\n{core['note']}\n")
    print("FLAG:", core["pattern"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

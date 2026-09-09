#!/usr/bin/env python3
"""invisible_ink — reference solver.

Reads index.js, collects trailing whitespace per line (space = 0, tab = 1,
MSB first), decodes the hidden module, then unseals the flag with the
version key found inside that module.

    python3 admin/solve.py [handout_dir|index.js] [--emit-payload]
"""

import base64
import os
import re
import sys


def extract_bits(path: str) -> str:
    with open(path, "r", newline="") as f:
        text = f.read()
    bits = []
    for line in text.split("\n"):
        m = re.search(r"[ \t]+$", line)
        if m:
            bits.append("".join("1" if c == "\t" else "0" for c in m.group(0)))
    return "".join(bits)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = args[0] if args else "handout"
    js = target if os.path.isfile(target) else os.path.join(target, "index.js")

    bits = extract_bits(js)
    if len(bits) == 0 or len(bits) % 8 != 0:
        raise SystemExit("no byte-aligned trailing-whitespace payload found")
    payload = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    src = payload.decode("ascii")

    if "--emit-payload" in sys.argv:
        print(src, end="")
        return

    blob = re.search(r'Buffer\.from\("([^"]+)","base64"\)', src)
    ver = re.search(r'const V="([^"]+)"', src)
    if not blob or not ver:
        raise SystemExit("decoded payload is not the seal module")
    raw = base64.b64decode(blob.group(1))
    key = ver.group(1).encode()
    flag = "".join(chr(b ^ key[i % len(key)]) for i, b in enumerate(raw))
    print(flag)


if __name__ == "__main__":
    main()

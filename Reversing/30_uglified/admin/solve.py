#!/usr/bin/env python3
"""uglified — reference solver.

Un-rotates the base64 string table in bundle.js, then tries every
(target, key) pair by length: the key decodes to exactly 16 bytes, the
target to 20–60 bytes. Each pair is inverted through the position mask
(parsed from the check loop, defaults 0x1f/0x03) and the first candidate
that the bundle itself accepts wins.

    python3 admin/solve.py [handout_dir|bundle.js]
"""

import base64
import os
import re
import subprocess
import sys

KEY_LEN = 16


def parse_bundle(path: str):
    with open(path) as f:
        src = f.read()
    m = re.search(r"var _0x[0-9a-f]{4}=\[(.*?)\];", src)
    if not m:
        raise SystemExit("string table not found")
    entries = re.findall(r"'([^']*)'", m.group(1))
    c = re.search(r"\}\(_0x[0-9a-f]{4},0x([0-9a-fA-F]+)\)", src)
    count = int(c.group(1), 16) if c else 0
    # Replicate the runtime IIFE: push(shift()) x count = left rotation.
    count %= len(entries)
    entries = entries[count:] + entries[:count]
    blobs = [base64.b64decode(e) for e in entries]
    mask = None
    for mm in re.finditer(r"0x([0-9a-fA-F]+)\+0x([0-9a-fA-F]+)", src):
        # The check loop is the one sharing a line with charCodeAt.
        line_start = src.rfind("\n", 0, mm.start()) + 1
        line_end = src.find("\n", mm.end())
        if "charCodeAt" in src[line_start:line_end]:
            mask = (int(mm.group(1), 16), int(mm.group(2), 16))
            break
    if mask is None:
        mask = (0x1F, 0x03)
    return blobs, mask


def invert(tgt: bytes, key: bytes, mask) -> bytes:
    a, b = mask
    return bytes(
        t ^ key[i % len(key)] ^ ((i * a + b) & 0xFF)
        for i, t in enumerate(tgt)
    )


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "handout"
    bundle = (target if os.path.isfile(target)
              else os.path.join(target, "bundle.js"))
    blobs, mask = parse_bundle(bundle)
    tgts = [x for x in blobs if 20 <= len(x) <= 60]
    keys = [x for x in blobs if len(x) == KEY_LEN]
    for tgt in tgts:
        for key in keys:
            body = invert(tgt, key, mask)
            try:
                text = body.decode("ascii")
            except UnicodeDecodeError:
                continue
            if not re.fullmatch(r"[a-z0-9_]+", text):
                continue
            cand = "cyber_quest{%s}" % text
            r = subprocess.run(["node", bundle, cand],
                               capture_output=True, text=True)
            if r.returncode == 0 and cand in r.stdout:
                print(cand)
                return
    raise SystemExit("no accepted receipt found")


if __name__ == "__main__":
    main()

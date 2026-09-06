#!/usr/bin/env python3
"""core_values — deterministic handout generator.

Compiles deployment/valuesd.c, runs it, and ships the heap dump it
produces (valuesd_heap.raw). The binary is NOT shipped; the dump is the
handout. Requires a C compiler and Linux (the dump is a /proc/self/mem
snapshot of the process' own [heap] mapping).
"""

import os
import subprocess
import shutil
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)
    out = os.path.join(HANDOUT, "valuesd_heap.raw")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["cc", "-O0", "-o", os.path.join(tmp, "valuesd"),
                        os.path.join(HERE, "valuesd.c")], check=True)
        subprocess.run([os.path.join(tmp, "valuesd")], cwd=tmp, check=True,
                       stdout=subprocess.DEVNULL)
        shutil.move(os.path.join(tmp, "valuesd_heap.raw"), out)

    # identity guard: the dump must not name the build machine
    blob = open(out, "rb").read()
    for marker in (b"dijith", b"celestia", b"/tmp/tmp"):
        if marker in blob:
            raise SystemExit(f"identity leak in valuesd_heap.raw: {marker!r}")

    print("handout written to", os.path.normpath(out))


if __name__ == "__main__":
    main()

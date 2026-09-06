#!/usr/bin/env python3
"""unsaved_changes — reference solve.

Simulates the documented solve path against a directory containing the
handout: the on-disk file is clean, the vim undo file still holds every
state, so loading it and stepping back one file-write recovers the
flagged draft. The pasted flag is hex (QA pre-hexed it to slip past the
mail keyword alerts), so the recovered line still needs one decode.

    python3 admin/solve.py /path/to/dir
"""

import binascii
import os
import re
import subprocess
import sys
import tempfile

RECOVER_VIM = """\
set undofile undodir=.
set directory=.
set encoding=utf-8
e standup_notes.md
earlier 1f
w! recovered.md
q
"""

FLAG_RE = re.compile(r"cyber_quest\{[^}]*\}")
HEX_RE = re.compile(r"\b([0-9a-f]{40,})\b")


def solve(directory: str) -> str:
    clean = open(os.path.join(directory, "standup_notes.md")).read()
    if "cyber_quest{" in clean:
        raise SystemExit("the shipped file is not supposed to contain the flag")
    print("standup_notes.md (on disk): clean — no flag")

    # path 1: strings over the swap snapshot (the crude route)
    swp = os.path.join(directory, ".standup_notes.md.swp")
    leak = subprocess.run(["strings", swp], capture_output=True, text=True).stdout
    m = HEX_RE.search(leak)
    if not m:
        raise SystemExit("swap snapshot does not leak the hex line")
    crude = binascii.unhexlify(m.group(1)).decode()
    print(f".standup_notes.md.swp  (strings+decode): {crude}")

    # path 2: the intended route — vim replays the undo history
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("standup_notes.md", ".standup_notes.md.un~"):
            subprocess.run(["cp", os.path.join(directory, name), tmp], check=True)
        with open(os.path.join(tmp, "recover.vim"), "w") as f:
            f.write(RECOVER_VIM)
        subprocess.run(
            ["vim", "-es", "-u", "NONE", "--not-a-term", "-S", "recover.vim"],
            cwd=tmp, check=True, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        rec = open(os.path.join(tmp, "recovered.md")).read()
    m = HEX_RE.search(rec)
    if not m:
        raise SystemExit("undo replay did not recover the hex line")
    flag = binascii.unhexlify(m.group(1)).decode()
    if not FLAG_RE.fullmatch(flag):
        raise SystemExit(f"decoded line is not a flag: {flag!r}")
    print(f".standup_notes.md.un~ (:earlier 1f, decoded): {flag}")
    return flag


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "handout"
    print(solve(d))

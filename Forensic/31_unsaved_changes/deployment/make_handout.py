#!/usr/bin/env python3
"""unsaved_changes — deterministic handout generator.

Regenerates everything in ../handout/ by driving real vim (Ex mode, no tty)
through the incident: the badge flag gets pasted into the standup notes, the
swap file is snapshotted mid-incident, the lines are deleted, the clean
version is written, and vim exits — leaving the persistent undo file behind.

Nothing here is secret; the solve path is documented in admin/solution.md.
Requires vim on PATH (the handout IS a vim artifact, so this is fair).
"""

import os
import re
import shutil
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{uns4ved_n0t3s_r3m3mb3r_3v3ryth1ng_5a91c4}"
FLAG_HEX = FLAG.encode().hex()

SEED = """\
# standup notes — week of 2013-08-19
* ledgerline migration still "in progress" (week 6)
* kevin says the printer is fine. the printer is not fine.
* the all-hands deck is due Thursday. it is not started. it is Thursday-adjacent.
"""

BUILD_VIM = """\
set undofile undodir=.
set directory=.
set encoding=utf-8
e standup_notes.md
" churn: three rewrites of the printer line so the undo chain has depth
call setline(3, '* kevin says the printer is fine (updated: mostly fine).')
w
call setline(3, '* kevin says the printer is fine (update: fine, per kevin).')
w
" the incident: qa finds the flag and it gets pasted into the standup notes,
" pre-hexed so the mail DLP keyword alerts do not file a ticket about it
call append(4, ['* qa found the badge flag. pasting it here as hex so the mail keyword alerts miss it:', '* {flaghex}', '* (that is hex. decode it before the deck. do NOT put this in the all-hands deck.)', '* (kevin: this is exactly why we do not have nice things)'])
w
" snapshot the swap mid-incident, while the flagged buffer is still live
silent !cp .standup_notes.md.swp swp_snapshot.swp
" the cover-up: delete the lines, write the clean version, quit
5,8d
w
q
"""

# The swap header records who and where: replace the build machine's
# identity (user, hostname, absolute temp path) with the story's — the
# editor session happened on kevin's laptop, started from the notes
# folder. The b0VIM header fields are fixed-width; every replacement is
# the same byte length (or NUL-shrunk inside its NUL padding), because
# vim validates the layout on recovery.
SWAP_PATCHES = [
    (re.compile(rb"\bdijith\b"), b"okafor"),
    (re.compile(rb"\bcelestia\b"), b"lt-oe442"),
    (re.compile(rb"/tmp/tmp[A-Za-z0-9_]+/standup_notes\.md"), b"standup_notes.md"),
]


def patch_swap(path: str) -> None:
    """Rewrite the identity fields in the b0VIM header (first 1 KiB only)."""
    with open(path, "rb") as f:
        head = bytearray(f.read(1024))
    for pat, new in SWAP_PATCHES:
        m = pat.search(head)
        if not m:
            raise SystemExit(f"swap header: expected field {pat!r} not found")
        old = m.group(0)
        if len(new) != len(old):
            # only NUL-shrink or equal-length swaps are safe: growing into
            # padding is not (vim validates the fixed-width field layout)
            if len(new) > len(old):
                raise SystemExit(f"replacement {new!r} longer than field {old!r}")
        head[m.start():m.end()] = new + b"\x00" * (len(old) - len(new))
    with open(path, "r+b") as f:
        f.write(head)
    final = open(path, "rb").read(1024)
    for marker in (b"dijith", b"celestia", b"/tmp/"):
        if marker in final:
            raise SystemExit(f"identity leak survives in swap header: {marker!r}")


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)
    for name in ("standup_notes.md", ".standup_notes.md.swp",
                 ".standup_notes.md.un~"):
        path = os.path.join(HANDOUT, name)
        if os.path.exists(path):
            os.remove(path)

    script = BUILD_VIM.format(flaghex=FLAG_HEX)
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "standup_notes.md"), "w") as f:
            f.write(SEED)
        with open(os.path.join(tmp, "build.vim"), "w") as f:
            f.write(script)
        subprocess.run(
            ["vim", "-es", "-u", "NONE", "--not-a-term", "-S", "build.vim"],
            cwd=tmp, check=True, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

        # sanity: the cover-up must be complete in the written file
        final = open(os.path.join(tmp, "standup_notes.md")).read()
        if FLAG in final:
            raise SystemExit("final file still contains the flag — cover-up failed")
        for name in ("standup_notes.md", ".standup_notes.md.un~",
                     "swp_snapshot.swp"):
            src = os.path.join(tmp, name)
            if not os.path.exists(src):
                raise SystemExit(f"vim did not produce {name}")

        shutil.copy(os.path.join(tmp, "standup_notes.md"), HANDOUT)
        shutil.copy(os.path.join(tmp, "swp_snapshot.swp"), HANDOUT + "/.swp.tmp")
        patch_swap(HANDOUT + "/.swp.tmp")
        os.replace(HANDOUT + "/.swp.tmp", os.path.join(HANDOUT, ".standup_notes.md.swp"))
        shutil.copy(os.path.join(tmp, ".standup_notes.md.un~"), HANDOUT)

    # sanity: the shipped artifacts must not name the build machine
    for name in (".standup_notes.md.swp", ".standup_notes.md.un~"):
        blob = open(os.path.join(HANDOUT, name), "rb").read()
        for marker in (b"dijith", b"celestia", b"/tmp/tmp"):
            if marker in blob:
                raise SystemExit(f"identity leak in {name}: {marker!r}")
    undo = open(os.path.join(HANDOUT, ".standup_notes.md.un~"), "rb").read()
    if FLAG.encode() in undo:
        raise SystemExit("flag is plain text in the undo file — encode it first")

    print("handout written to", os.path.normpath(HANDOUT))


if __name__ == "__main__":
    main()

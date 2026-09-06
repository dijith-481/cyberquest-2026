#!/usr/bin/env python3
"""incognito — reference solve.

Simulates the documented solve path against a directory containing the
handout: confirm the History DB reads clean through SQLite, then carve
the flagged (deleted) row out of the never-checkpointed WAL, with the
disk cache as the corroborating second path.

    python3 admin/solve.py /path/to/handout
"""

import os
import re
import sqlite3
import sys
import tempfile
import shutil

FLAG_RE = re.compile(rb"cyber_quest\{[^}]*\}")


def solve(directory: str) -> str:
    profile = os.path.join(directory, "profile")

    # path 1: sqlite shows the "wiped" state — history reads clean
    con = sqlite3.connect(f"file:{os.path.join(profile, 'History')}?mode=ro", uri=True)
    rows = con.execute("SELECT count(*) FROM urls").fetchone()[0]
    flagged = con.execute(
        "SELECT count(*) FROM urls WHERE url LIKE '%cyber_quest%'").fetchone()[0]
    print(f"History via sqlite: {rows} rows remain, {flagged} contain a flag")
    con.close()
    assert flagged == 0, "the wipe did not take — handout is wrong"

    # path 2 (intended): the WAL was never checkpointed; carve the deleted
    # page images out of it
    wal = open(os.path.join(profile, "History-wal"), "rb").read()
    hits = sorted(set(m.group(0).decode() for m in FLAG_RE.finditer(wal)))
    print(f"History-wal carve: {len(hits)} distinct flag-shaped string(s)")
    if not hits:
        raise SystemExit("flag not recoverable from WAL")
    flag = hits[0]

    # path 3 (corroboration): the disk cache folder was never in scope
    for name in sorted(os.listdir(os.path.join(profile, "Cache"))):
        body = open(os.path.join(profile, "Cache", name), "rb").read()
        m = FLAG_RE.search(body)
        if m:
            print(f"Cache/{name} carve: {m.group(0).decode()}")

    print("flag:", flag)
    return flag


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "handout"
    print(solve(d))

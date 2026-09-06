#!/usr/bin/env python3
"""dig_site — reference solve.

Simulates the documented solve path: list unreachable commits with
`git fsck --lost-found`, inspect each candidate import, and pull the
calibration phrase out of the boring-looking one.

    python3 admin/solve.py /path/to/skills_archive
"""

import re
import subprocess
import sys

FLAG_RE = re.compile(r"cyber_quest\{[^}]*\}")


def git(repo: str, *args: str, text=True) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True,
                          capture_output=True, text=text).stdout


def solve(repo: str) -> str:
    log = git(repo, "log", "--oneline")
    print(f"reachable history: {len(log.splitlines())} commits, all dated 1984-1989")

    fsck = git(repo, "fsck", "--lost-found")
    dangling = [l.split()[-1] for l in fsck.splitlines()
                if "dangling commit" in l]
    print(f"dangling commits found by fsck: {len(dangling)}")

    found = []
    for sha in dangling:
        files = git(repo, "show", "--name-only", "--format=", sha).split()
        for path in files:
            blob = git(repo, "show", f"{sha}:{path}")
            m = FLAG_RE.search(blob)
            label = git(repo, "show", "-s", "--format=%s", sha).strip()
            if m:
                print(f"  {sha[:8]}  {label!r}  -> {path}  CONTAINS PHRASE")
                found.append((sha, path, m.group(0)))
            else:
                print(f"  {sha[:8]}  {label!r}  -> {path}  (decoy)")

    if len(found) != 1:
        raise SystemExit(f"expected exactly one real candidate, got {len(found)}")
    sha, path, flag = found[0]
    print(f"flag (from {path} on {sha[:8]}): {flag}")
    return flag


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "handout/skills_archive"
    print(solve(d))

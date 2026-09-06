#!/usr/bin/env python3
"""dig_site — reference solve.

Simulates the documented solve path against a COPY of the handout repo
(the reference solve mutates it: it runs `git index-pack`):

  1. `git fsck` -> dangling commits; the cold-storage receipt names a
     pack whose .idx never shipped.
  2. `git index-pack` the idx-less pack -> the cold import history
     becomes readable (still unreachable).
  3. The cold tip adds skills/spreadsheet_divination.md, but the blob
     was never packed — only its sha survives in the tree.
  4. The blob exists as a loose object with the zlib header stripped;
     raw-inflating it yields the flag.

    python3 admin/solve.py /path/to/skills_archive
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import zlib

FLAG_RE = re.compile(r"cyber_quest\{[^}]*\}")


def git(repo: str, *args: str, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, check=check,
                          capture_output=True, text=True)


def solve(src_repo: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "skills_archive")
        shutil.copytree(src_repo, repo)

        log = git(repo, "log", "--oneline").stdout
        print(f"reachable history: {len(log.splitlines())} commits, all 1984-1989")

        # 1. the dangling commits — one of them is a receipt
        fsck = (git(repo, "fsck", check=False).stdout
                + git(repo, "fsck", check=False).stderr)
        dangles = [l.split()[-1] for l in fsck.splitlines()
                   if "dangling commit" in l]
        print(f"dangling commits: {len(dangles)}")
        receipt, pack_name = None, None
        for sha in dangles:
            names = git(repo, "show", "--name-only", "--format=", sha,
                        check=False).stdout.split()
            if "cold_storage_receipt.txt" in names:
                receipt = sha
                body = git(repo, "show", f"{sha}:cold_storage_receipt.txt").stdout
                pack_name = re.search(r"(pack-[0-9a-f]+\.pack)", body).group(1)
            else:
                label = git(repo, "show", "-s", "--format=%s", sha).stdout.strip()
                print(f"  decoy: {sha[:8]} {label!r}")
        if not pack_name:
            raise SystemExit("no cold-storage receipt among dangling commits")
        print(f"receipt ({receipt[:8]}): pack {pack_name} shipped without .idx")

        # 2. revive the pack
        pack = os.path.join(repo, ".git", "objects", "pack", pack_name)
        git(repo, "index-pack", pack, check=True)
        print("pack indexed; cold history readable but unreachable")

        # 3. find the cold tip among the now-visible unreachable commits
        fsck = git(repo, "fsck", "--unreachable", check=False)
        unreach = [l.split()[-1] for l in (fsck.stdout + fsck.stderr).splitlines()
                   if "unreachable commit" in l]
        tip = None
        for sha in unreach:
            if git(repo, "log", "-1", "--format=%s", sha,
                   check=False).stdout.strip() == "cold: calibrate":
                tip = sha
        if not tip:
            raise SystemExit("cold tip not found after indexing")
        git(repo, "log", "--oneline", tip)
        blob = git(repo, "ls-tree", "-r", tip, "--",
                   "skills/spreadsheet_divination.md").stdout.split()[2]
        print(f"cold tip {tip[:8]} -> blob {blob}")
        if git(repo, "cat-file", "-p", blob, check=False).returncode == 0:
            raise SystemExit("blob unexpectedly readable — should be corrupt")

        # 4. the damaged loose object: zlib header stripped, raw deflate left
        obj = os.path.join(repo, ".git", "objects", blob[:2], blob[2:])
        raw = open(obj, "rb").read()
        payload = zlib.decompressobj(-15).decompress(raw).decode()
        m = FLAG_RE.search(payload)
        if not m:
            raise SystemExit(f"no flag in inflated payload: {payload!r}")
        print(f"raw-inflated {obj}: flag recovered")
        return m.group(0)


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "handout/skills_archive"
    print(solve(d))

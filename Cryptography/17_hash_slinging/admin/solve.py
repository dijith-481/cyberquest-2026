#!/usr/bin/env python3
"""hash_slinging — scripted solve.

Path:
  1. Plain-MD5 wordlist crack of the standard staff rows.
  2. Read the IT memo -> executive rotation scheme
     <BaseWord><Season><YY><symbol>, keyed off the CSV last_changed date.
  3. Targeted candidate generation for the Executive row.
  4. XOR-decrypt vault_note.txt with the cracked password (policy EX-3).

Usage:
    python3 solve.py [HANDOUT_DIR]     # default: ../handout
"""

import csv
import hashlib
import os
import sys

HANDOUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "handout")
SYMBOLS = "!@#"
SEASONS = ("Winter", "Spring", "Summer", "Autumn")  # Dec–Feb, Mar–May, ...


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def xor(data: bytes, key: str) -> bytes:
    k = key.encode()
    return bytes(b ^ k[i % len(k)] for i, b in enumerate(data))


def load_rows():
    with open(os.path.join(HANDOUT, "credential_audit.csv"), newline="") as f:
        return list(csv.DictReader(f))


def load_wordlist():
    with open(os.path.join(HANDOUT, "corporate_wordlist.txt")) as f:
        return [w.strip() for w in f if w.strip()]


def staff_candidates(word: str):
    """Trivial mutation rules for standard staff passwords."""
    yield word
    yield word.lower()
    for n in range(0, 100):
        yield f"{word}{n}"
        yield f"{word}{n}!"


def main() -> int:
    rows = load_rows()
    words = load_wordlist()
    hashes = {r["md5_hash"]: r for r in rows}

    # -- stage 1: wordlist crack of standard staff -------------------------
    cracked = {}
    for w in words:
        for cand in staff_candidates(w):
            h = md5(cand)
            if h in hashes and h not in cracked:
                cracked[h] = cand
    print(f"[1] staff rows cracked: {len(cracked)}")

    # -- stage 2: executive rotation scheme --------------------------------
    execs = [r for r in rows if r["department"] == "Executive" and r["md5_hash"] not in cracked]
    print(f"[2] exec rows remaining: {len(execs)} -> {execs[0]['name']!r}")

    for row in execs:
        year = int(row["last_changed"][:4]) % 100
        month = int(row["last_changed"][5:7])
        season = SEASONS[((month + 1) % 12) // 3]  # Dec/Jan/Feb -> Winter ...
        for base in words:
            for sym in SYMBOLS:
                cand = f"{base}{season}{year:02d}{sym}"
                if md5(cand) == row["md5_hash"]:
                    cracked[row["md5_hash"]] = cand
                    password = cand
                    print(f"[3] cracked {row['name']!r}: {password}")

    # -- stage 3: open the vault note ---------------------------------------
    target = next(r for r in rows if r["department"] == "Executive")
    password = cracked[target["md5_hash"]]
    sealed = bytes.fromhex(open(os.path.join(HANDOUT, "vault_note.txt")).read().strip())
    note = xor(sealed, password).decode("utf-8", "replace")
    print("[4] vault note:")
    print(note)

    for line in note.splitlines():
        if line.startswith("Flag:"):
            print("FLAG:", line.split("Flag: ", 1)[1].strip())
            return 0
    print("!! flag not found in note")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

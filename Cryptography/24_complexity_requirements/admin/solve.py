#!/usr/bin/env python3
"""complexity_requirements — scripted solve.

  1. Read the policy memo: stored credentials are SHA-256 over
     "salt:password", and salts are *derived* from employee metadata
     (<DEPT>-<EMPID>-Q<quarter>-<YY>) — fully predictable.
  2. Read the helpdesk card: compliant passwords are
     <BaseWord><Season><YY><symbol> over the 60-word approved wordlist.
     The "strong" policy space is 60 x 4 x 2 x 3 = 1,440 candidates.
  3. Crack every row whose salt is in the export.
  4. The Director's row (EX-0007) exported with salt "#N/A": reconstruct
     the salt from the derivation rule (EX, 0007, last_changed
     2026-04-14 -> Q2, YY 26) and crack it too.
  5. Unseal the break-glass note (policy EX-3: XOR with the owner's
     password) with the Director's password and read the flag.

Usage:
    python3 solve.py [HANDOUT_DIR]     # default: ../handout
"""

import csv
import hashlib
import os
import sys

HANDOUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "handout")

SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
SYMBOLS = ["!", "@", "#"]
YEARS = ["25", "26"]


def quarter(date: str) -> tuple[int, int]:
    q = (int(date[5:7]) - 1) // 3 + 1
    return q, int(date[2:4])


def derive_salt(emp_id: str, dept: str, changed: str) -> str:
    q, yy = quarter(changed)
    return f"{dept}-{emp_id.split('-')[1]}-Q{q}-{yy:02d}"


def hash_pw(salt: str, password: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def main() -> int:
    words = [w.strip() for w in open(os.path.join(HANDOUT, "corporate_wordlist.txt")) if w.strip()]
    card = open(os.path.join(HANDOUT, "helpdesk_card.txt")).read()
    memo = open(os.path.join(HANDOUT, "security_memo_2026.txt")).read()
    assert "SHA-256" in memo and "derived" in memo and "<BaseWord>" in card

    candidates = [f"{w.capitalize()}{s}{y}{x}" for w in words for s in SEASONS for y in YEARS for x in SYMBOLS]
    print(f"[1] policy-compliant candidate space: {len(candidates)} passwords")

    rows = list(csv.DictReader(open(os.path.join(HANDOUT, "password_export.csv"))))
    print(f"[2] hashing {len(candidates)} candidates per row across {len(rows)} rows")

    def crack(salt: str, target: str) -> str | None:
        for pw in candidates:
            if hash_pw(salt, pw) == target:
                return pw
        return None

    cracked = {}
    for r in rows:
        salt = r["salt"]
        if salt == "#N/A":
            salt = derive_salt(r["employee_id"], r["department"], r["last_changed"])
            print(f"[4] {r['employee_id']}: salt not exported — derived {salt} from the memo rule")
        pw = crack(salt, r["sha256"])
        if pw is not None:
            cracked[r["employee_id"]] = (pw, salt)
    print(f"[3] cracked {len(cracked)} of {len(rows)} rows (compliant-but-weak; the rest are actually strong)")
    for emp_id in sorted(cracked):
        pw, salt = cracked[emp_id]
        print(f"    {emp_id}  salt={salt}  password={pw}")

    director_id = "EX-0007"  # the row the export glitched on
    if director_id not in cracked:
        print("!! Director row not cracked")
        return 1
    director_pw = cracked[director_id][0]
    print(f"[4] Director's password: {director_pw}")

    blob = bytes.fromhex(open(os.path.join(HANDOUT, "break_glass_note.txt.enc")).read().strip())
    kb = director_pw.encode()
    note = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(blob)).decode()
    print("[5] break-glass note:\n")
    print(note)

    for line in note.splitlines():
        if line.startswith("Flag:"):
            print("FLAG:", line.split("Flag: ", 1)[1].strip())
            return 0
    print("!! flag not found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

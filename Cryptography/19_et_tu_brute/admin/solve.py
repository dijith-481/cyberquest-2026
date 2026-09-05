#!/usr/bin/env python3
"""et_tu_brute — scripted solve.

  1. Break the cover sheet's Caesar shift (chi-squared over English).
  2. Read the cover: the body is a repeating-key Vigenere, and every memo
     opens with the standard header MEMORANDUM ORDINARY ENGINEERING.
  3. Use the 29-letter crib at position 0 to derive the key stream, then
     find every key length for which the stream is consistent — that
     recovers the full keyphrase without guessing it.
  4. Decrypt the body.

Usage:
    python3 solve.py [HANDOUT_DIR]     # default: ../handout
"""

import os
import string
import sys

HANDOUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "handout")

CRIB = "MEMORANDUMORDINARYENGINEERING"

FREQ = {  # rough English letter frequencies (percent)
    "E": 12.7, "T": 9.1, "A": 8.2, "O": 7.5, "I": 7.0, "N": 6.7,
    "S": 6.3, "H": 6.1, "R": 6.0, "D": 4.3, "L": 4.0, "C": 2.8,
    "U": 2.8, "M": 2.4, "W": 2.4, "F": 2.2, "G": 2.0, "Y": 2.0,
    "P": 1.9, "B": 1.5, "V": 1.0, "K": 0.8, "J": 0.15, "X": 0.15,
    "Q": 0.1, "Z": 0.07,
}


def chi_squared(text: str) -> float:
    n = len(text)
    if n == 0:
        return float("inf")
    score = 0.0
    for ch, pct in FREQ.items():
        score += (text.count(ch) - pct / 100 * n) ** 2 / (pct / 100 * n)
    return score


def caesar_break(ciphertext: str) -> tuple[int, str]:
    letters = [c for c in ciphertext.upper() if c in string.ascii_uppercase]
    best = None
    for shift in range(26):
        dec = "".join(chr((ord(c) - 65 - shift) % 26 + 65) for c in letters)
        score = chi_squared(dec)
        if best is None or score < best[0]:
            best = (score, shift, dec)
    return best[1], best[2]


def shift_str(c: str, p: str) -> str:
    """key letter that turns plaintext letter p into ciphertext letter c"""
    return chr((ord(c) - ord(p)) % 26 + ord("A"))


def unshift(c: str, k: str) -> str:
    return chr((ord(c) - ord(k)) % 26 + ord("A"))


def vigenere_decrypt(ciphertext: str, key: str) -> str:
    out, ki = [], 0
    for ch in ciphertext:
        if ch in string.ascii_letters:
            k = key[ki % len(key)]
            lo = ch.lower()
            dec = chr((ord(lo) - ord(k.lower())) % 26 + ord("a"))
            out.append(dec.upper() if ch.isupper() else dec)
            ki += 1
        else:
            out.append(ch)
    return "".join(out)


def main() -> int:
    cover = open(os.path.join(HANDOUT, "memo_cover.txt")).read()
    body = open(os.path.join(HANDOUT, "memo_body.txt")).read()

    # -- stage 1: break the cover ------------------------------------------
    shift, cover_plain = caesar_break(cover)
    print(f"[1] cover Caesar shift = {shift}")
    print(cover_plain)

    # -- stage 2: crib-derive the key stream --------------------------------
    body_letters = [c for c in body if c.isalpha()]
    stream = "".join(shift_str(c.upper(), p) for c, p in zip(body_letters, CRIB))
    print(f"[2] crib-derived key stream ({len(stream)} chars): {stream}")

    # -- stage 3: consistent key lengths ------------------------------------
    candidates = []
    for L in range(1, len(CRIB) + 1):
        key = stream[:L]
        if all(stream[i] == key[i % L] for i in range(len(stream))):
            candidates.append(key)
    # keep only minimal keys (not repeats of a shorter consistent key)
    minimal = []
    for k in candidates:
        if not any(len(c) < len(k) and len(k) % len(c) == 0 and k.startswith(c)
                   for c in candidates):
            minimal.append(k)
    print(f"[3] consistent key lengths: {[len(k) for k in minimal]} -> {minimal}")

    key = minimal[0]

    # -- stage 4: decrypt ----------------------------------------------------
    plain = vigenere_decrypt(body, key)
    print(f"[4] body decrypted with key {key}:\n")
    print(plain)

    for line in plain.splitlines():
        if line.startswith("Flag:"):
            print("FLAG:", line.split("Flag: ", 1)[1].strip())
            return 0
    print("!! flag not found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

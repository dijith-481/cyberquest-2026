#!/usr/bin/env python3
"""et_tu_brute — deterministic handout generator.

Writes handout/memo_cover.txt (Caesar shift 11) and handout/memo_body.txt
(Vigenere, keyphrase VENIVIDICI, letters-only keyed, case preserved).

The cover sheet never reveals the keyphrase — only that the body cipher is
"the General's favorite", that it is a repeating-key shift, and that every
memo body opens with the standard header MEMORANDUM ORDINARY ENGINEERING.
That header is the crib. The keyphrase is Latin, which is a second (braver)
path.

    python3 deployment/make_memo.py
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

CAESAR_SHIFT = 11
KEYPHRASE = "VENIVIDICI"

FLAG = "cyber_quest{3t_tu_k3ybrut3_b4072a}"

COVER_PLAIN = """ORDINARY ENGINEERING - RECEIVING DESK
COVER SHEET FOR INTEROFFICE MEMO 77-C
ROUTED AS: GENERAL CORRESPONDENCE - ROUTINE

The attached memo body is sealed the way the General likes it: a repeating
key, shifted by word, letters only, punctuation rides along untouched. We
are not permitted to know the key, and honestly nobody here wants it.

Two facts survive the sealing process and are printed here for the courier:

1. Every memo body opens with the standard header: MEMORANDUM ORDINARY
   ENGINEERING. The header is standardized, ceremonial, and — this is the
   part Legal hates — standardized in plaintext terms.

2. The keyphrase is Latin. Per a tradition nobody can justify and nobody
   has been able to stop.

Deliver to Legal. Legal will pretend to read it.
"""

BODY_PLAIN = """MEMORANDUM ORDINARY ENGINEERING
FROM: OFFICE OF THE GENERAL COUNSEL
RE: THE PATTERN, THE PIPELINE, AND THE OTHER THING KEVIN SEALED

Legal has reviewed the asset-transfer-pipeline export that circulated last
week and has concluded, after considerable effort, that nobody in this
building has the training to call it encryption. We are therefore calling
it a pattern. The pattern is a pattern. This sentence has been approved.

Three rulings:

1. The vault note is a note. Its seal is a seal. Nobody is to put that in
   writing, which is why this memo is not in writing.

2. The onion is compliant, because compliance tested only the outermost
   layer. This is also, incidentally, how we test the fire exits.

3. Kevin's standing proposal that the company adopt an actual cipher is
   denied for the fourth year running. The ceremony flag is reproduced
   below in the usual scoreboard dialect, and if it leaks again we will
   simply characterize the leak as a drill.

Flag: {flag}

Signed,
the General Counsel (acting, since the incident)
"""


def caesar(text: str, shift: int) -> str:
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + shift) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + shift) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)


def vigenere(text: str, key: str) -> str:
    out = []
    k = key.upper()
    ki = 0
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + ord(k[ki % len(k)]) - 65) % 26 + 97))
            ki += 1
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + ord(k[ki % len(k)]) - 65) % 26 + 65))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)
    with open(os.path.join(HANDOUT, "memo_cover.txt"), "w") as f:
        f.write(caesar(COVER_PLAIN, CAESAR_SHIFT))
    with open(os.path.join(HANDOUT, "memo_body.txt"), "w") as f:
        f.write(vigenere(BODY_PLAIN.format(flag=FLAG), KEYPHRASE))
    print("handout written:", os.path.normpath(HANDOUT))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Off Key -- scripted solve.

The handout is three paragraphs, each typed by someone fluent in one
layout while the machine was set to the next one in the chain
QWERTY -> Dvorak -> Colemak -> QWERTY. Approach:

  1. Decode each paragraph with every layout-to-layout transform and keep
     the decoding that best matches a known Fast Car lyric excerpt.
  2. Diff each decoded paragraph against the genuine excerpt. The changed
     words, in reading order, are the flag payload.
  3. Leetify the whole payload and wrap it.

Usage:
    python3 solve.py [handout/transcripts.txt]
"""

from __future__ import annotations

import string
import sys
from pathlib import Path

# ------------------------------------------------------------------ layouts
QWERTY_ROWS = (
    "qwertyuiop[]",
    "asdfghjkl;'",
    "zxcvbnm,./",
)

LAYOUT_ROWS = {
    "qwerty": QWERTY_ROWS,
    "dvorak": ("',.pyfgcrl/=", "aoeuidhtns-", ";qjkxbmwvz"),
    "colemak": ("qwfpgjluy;[]", "arstdhneio'", "zxcvbkm,./"),
}

LAYOUTS = tuple(LAYOUT_ROWS)


def transform(a: str, b: str) -> dict[str, str]:
    """Layout-a output char -> layout-b output char on the same key."""
    ca, cb = {}, {}
    for qrow, arow, brow in zip(QWERTY_ROWS, LAYOUT_ROWS[a], LAYOUT_ROWS[b]):
        for qch, ach, bch in zip(qrow, arow, brow):
            ca[qch] = ach
            cb[qch] = bch
    return {ca[qch]: cb[qch] for qch in ca}


AUTHENTIC = (
    [
        "I want a ticket to anywhere",
        "Maybe we make a deal",
        "Maybe together we can get somewhere",
        "Any place is better",
        "Starting from zero got nothing to lose",
        "Maybe we'll make something",
        "Me, myself, I got nothing to prove",
    ],
    [
        "I got a plan to get us outta here",
        "I been working at the convenience store",
        "Managed to save just a little bit of money",
        "Won't have to drive too far",
        "Just 'cross the border and into the city",
        "You and I can both get jobs",
        "And finally see what it means to be living",
    ],
    [
        "See, my old man's got a problem",
        "He live with the bottle, that's the way it is",
        "He says his body's too old for working",
        "His body's too young to look like his",
        "My mama went off and left him",
        "She wanted more from life than he could give",
        "I said somebody's got to take care of him",
        "So I quit school and that's what I did",
    ],
)

FULL_SONG = """\
You got a fast car
I want a ticket to anywhere
Maybe we make a deal
Maybe together we can get somewhere
Any place is better
Starting from zero got nothing to lose
Maybe we'll make something
Me, myself, I got nothing to prove
You got a fast car
I got a plan to get us outta here
I been working at the convenience store
Managed to save just a little bit of money
Won't have to drive too far
Just 'cross the border and into the city
You and I can both get jobs
And finally see what it means to be living
See, my old man's got a problem
He live with the bottle, that's the way it is
He says his body's too old for working
His body's too young to look like his
My mama went off and left him
She wanted more from life than he could give
I said somebody's got to take care of him
So I quit school and that's what I did
"""

LEET = {"a": "4", "o": "0", "t": "7", "e": "3"}


def convert(text: str, cmap: dict[str, str]) -> str:
    out: list[str] = []
    for ch in text:
        low = ch.lower()
        if low not in cmap:
            out.append(ch)
            continue
        mapped = cmap[low]
        if ch.isupper() and mapped.isalpha():
            mapped = mapped.upper()
        out.append(mapped)
    return "".join(out)


def words(text: str) -> list[str]:
    return [w.strip(string.punctuation).lower() for w in text.split()]


def score(decoded: str, authentic_lines: list[str]) -> int:
    got = words(decoded)
    want = words(" ".join(authentic_lines))
    return sum(a == b for a, b in zip(got, want))


def leetify(token: str) -> str:
    return "".join(LEET.get(c, c) for c in token)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("handout/transcripts.txt")
    raw = path.read_text()
    paragraphs = [p for p in raw.rstrip("\n").split("\n\n") if p.strip()]
    if len(paragraphs) != 3:
        print(f"expected 3 paragraphs, found {len(paragraphs)}", file=sys.stderr)
        return 1

    candidates = [(a, b) for a in LAYOUTS for b in LAYOUTS]
    payload: list[str] = []

    for para, authentic_lines in zip(paragraphs, AUTHENTIC):
        best, best_decoded, best_score = None, None, -1
        for a, b in candidates:
            decoded = convert(para, transform(a, b))
            s = score(decoded, authentic_lines)
            if s > best_score:
                best, best_decoded, best_score = (a, b), decoded, s
        total = len(words(" ".join(authentic_lines)))
        print(f"paragraph -> from={best[0]:<7} to={best[1]:<7} ({best_score}/{total} words match)")

        for aut_line, dec_line in zip(authentic_lines, best_decoded.split("\n")):
            for a, d in zip(aut_line.split(), dec_line.split()):
                if a.lower() != d.lower():
                    print(f"    swapped: {a!r} -> {d!r}")
                    payload.append(leetify(d.strip(string.punctuation).lower()))

    flag = "cyber_quest{" + "_".join(payload) + "}"
    print(f"\npayload: {' '.join(payload)}")
    print(flag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

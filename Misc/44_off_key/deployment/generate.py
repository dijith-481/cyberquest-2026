#!/usr/bin/env python3
"""Off Key -- seeded generator for Misc slot 44.

The handout is a plain text file of three typist transcripts. Each typist
was fluent in one layout but the machine was set to the next one in the
chain, so the wrong characters came out:

    paragraph 1:  QWERTY typist  -> Dvorak machine
    paragraph 2:  Dvorak typist  -> Colemak machine
    paragraph 3:  Colemak typist -> QWERTY machine

The pool also made four deliberate word swaps. Three are ordinary
English words that read, in order, "off key track" — the challenge name.
The fourth, last in reading order, is a random letter-and-number string:
the unique salt that finishes the flag. Leetify the three words
(a->4, o->0, t->7, e->3), keep the salt as-is, join with underscores and wrap
in cyber_quest{}.

    python3 deployment/generate.py --seed 44 --flag 'cyber_quest{...}' \
        --out handout/transcripts.txt [--zip 44_off_key.zip]

The output is deterministic for a given (seed, flag).
"""

from __future__ import annotations

import argparse
import random
import string
import zipfile
from pathlib import Path

# ------------------------------------------------------------------ layouts
# Physical key positions, written as the character the stock US QWERTY
# layout prints there. Every other layout is the same three rows read as
# the character that layout prints on the same physical key.
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


def layout_chars(name: str) -> dict[str, str]:
    """QWERTY output char -> this layout's output on the same key."""
    m: dict[str, str] = {}
    for qrow, lrow in zip(QWERTY_ROWS, LAYOUT_ROWS[name]):
        assert len(qrow) == len(lrow), (name, qrow, lrow)
        for qch, lch in zip(qrow, lrow):
            m[qch] = lch
    return m


def transform(a: str, b: str) -> dict[str, str]:
    """Layout-a output char -> layout-b output char on the same key."""
    ca, cb = layout_chars(a), layout_chars(b)
    return {ca[qch]: cb[qch] for qch in ca}


# ------------------------------------------------------------------ lyrics
# Verse 1 (excerpt), verse 2 (excerpt), verse 3. The two literal
# "You got a fast car" intro lines are intentionally dropped: if they were
# present the phrase would already exist in the decoded text and the word
# diff would be pointless. The rest is verbatim.
PARAGRAPHS = (
    {
        "machine": "dvorak",
        "lines": [
            "I want a ticket to anywhere",
            "Maybe we make a deal",
            "Maybe together we can get somewhere",
            "Any place is better",
            "Starting from zero got nothing to lose",
            "Maybe we'll make something",
            "Me, myself, I got nothing to prove",
        ],
    },
    {
        "machine": "colemak",
        "lines": [
            "I got a plan to get us outta here",
            "I been working at the convenience store",
            "Managed to save just a little bit of money",
            "Won't have to drive too far",
            "Just 'cross the border and into the city",
            "You and I can both get jobs",
            "And finally see what it means to be living",
        ],
    },
    {
        "machine": "qwerty",
        "lines": [
            "See, my old man's got a problem",
            "He live with the bottle, that's the way it is",
            "He says his body's too old for working",
            "His body's too young to look like his",
            "My mama went off and left him",
            "She wanted more from life than he could give",
            "I said somebody's got to take care of him",
            "So I quit school and that's what I did",
        ],
    },
)

# The machine each transcript was typed on. The typist was fluent in the
# layout one step back in the chain QWERTY -> Dvorak -> Colemak -> QWERTY.
TYPIST_LAYOUT = ("qwerty", "dvorak", "colemak")

# ------------------------------------------------------------------ swaps
# (paragraph, line, token index, authentic word, replacement). In reading
# order the real words spell OFF KEY TRACK; the random salt sits last.
SWAPS = (
    {"p": 0, "l": 2, "i": 2, "old": "we", "new": "off"},
    {"p": 1, "l": 1, "i": 4, "old": "the", "new": "key"},
    {"p": 2, "l": 0, "i": 6, "old": "problem", "new": "track"},
    {"p": 2, "l": 7, "i": 3, "old": "school", "new": "<salt>"},
)

FLAG_WORDS = ("off", "key", "track")
LEET = {"a": "4", "o": "0", "t": "7", "e": "3"}

# The full song, used only as a word set so the random salt can be told
# apart from a real word.
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

# Letters that the house-style leet never touches, so the salt survives
# the final conversion untouched.
SALT_LETTERS = "".join(c for c in string.ascii_lowercase if c not in "aot")
SALT_DIGITS = string.digits


def song_vocab() -> set[str]:
    return {w.strip(string.punctuation).lower() for w in FULL_SONG.split() if w}


def make_salt(rng: random.Random, length: int = 6) -> str:
    vocab = song_vocab()
    while True:
        token = "".join(rng.choice(SALT_LETTERS + SALT_DIGITS) for _ in range(length))
        if not any(c.isdigit() for c in token):
            continue
        if not any(c.isalpha() for c in token):
            continue
        if token.lower() in vocab:
            continue
        return token


def build_modified(salt: str) -> list[list[str]]:
    """Return the lyrics as paragraphs of space-split token lists."""
    by_key: dict[tuple[int, int], dict[int, str]] = {}
    for sw in SWAPS:
        by_key.setdefault((sw["p"], sw["l"]), {})[sw["i"]] = (
            salt if sw["new"] == "<salt>" else sw["new"]
        )

    out: list[list[str]] = []
    for p, para in enumerate(PARAGRAPHS):
        para_lines: list[str] = []
        for l, line in enumerate(para["lines"]):
            tokens = line.split()
            for i, new in by_key.get((p, l), {}).items():
                expected = next(
                    sw["old"] for sw in SWAPS
                    if sw["p"] == p and sw["l"] == l and sw["i"] == i
                )
                assert tokens[i] == expected, (p, l, i, tokens[i], expected)
                tokens[i] = new
            para_lines.append(" ".join(tokens))
        out.append(para_lines)
    return out


# ------------------------------------------------------------------ encode
def encode_text(text: str, cmap: dict[str, str]) -> str:
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


def build_transcript(seed: int) -> tuple[str, str]:
    rng = random.Random(f"{seed}|off-key-typing-pool")
    salt = make_salt(rng)
    modified = build_modified(salt)

    blocks: list[str] = []
    for typist, para, lines in zip(TYPIST_LAYOUT, PARAGRAPHS, modified):
        cmap = transform(typist, para["machine"])
        blocks.append("\n".join(encode_text(line, cmap) for line in lines))
    return "\n\n".join(blocks) + "\n", salt


def build_zip(transcript: str) -> bytes:
    import io

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        info = zipfile.ZipInfo("transcripts.txt", date_time=(2026, 9, 13, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.compress_level = 9
        z.writestr(info, transcript)
    return buf.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--flag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--zip", default=None)
    args = ap.parse_args()

    transcript, salt = build_transcript(args.seed)

    # the seed decides the salt, so the flag is fixed by the seed
    payload = "_".join("".join(LEET.get(c, c) for c in w) for w in FLAG_WORDS)
    expected = f"cyber_quest{{{payload}_{salt}}}"
    if args.flag != expected:
        raise SystemExit(f"flag mismatch: seed {args.seed} makes {expected}, got {args.flag}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(transcript)
    print(f"wrote {args.out} ({len(transcript)} bytes, seed {args.seed}, salt {salt!r})")

    if args.zip:
        Path(args.zip).parent.mkdir(parents=True, exist_ok=True)
        Path(args.zip).write_bytes(build_zip(transcript))
        print(f"wrote {args.zip}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""eigenface — deterministic handout generator.

Writes:
  handout/template_store.json    the breach dump (moduli, per-candidate leaks)
  handout/enrolment_notes.txt    the operator-facing note
  handout/manifest.txt           a small index so the ZIP is not nameless

The leak is a Hidden Number Problem. Every candidate's 64-bit enrolment key is
exposed through three (a, z) pairs where

    z = (a * key + e)  mod  q

with q a 256-bit prime and e a small signed residue, |e| < 2^17. The player has
to notice that the key is far narrower than the modulus, invert each leak, and
search the small error rather than the 2^64 keyspace.

Determinism: every value is derived from a fixed seed, so re-running produces
byte-identical files. verify.sh hashes the committed handout before regenerating
and fails on drift.
"""

import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{3y3_f4c3_m34r_th3_fl4t_fl0w3r}"

SEED = 20260930
KEY_BITS = 64
NOISE_BITS = 17
NOISE = 1 << NOISE_BITS
KEY_BOUND = 1 << KEY_BITS
LEAKS_PER_CANDIDATE = 4

# Candidate display names. Candidate 00 is the flag-holder; the rest are
# decoys whose keys are equally exposed, so "find the leak" and "find the
# right person" are the same amount of work.
NAMES = [
    "VISITOR-00", "VISITOR-01", "VISITOR-02", "VISITOR-03",
    "VISITOR-04", "VISITOR-05",
]
ADMIN_KEY = 0x9E3779B97F4A7C15


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def next_prime(n: int) -> int:
    while not is_prime(n):
        n += 2
    return n


def random_prime(rng: random.Random) -> int:
    n = rng.getrandbits(255) | (1 << 255) | 1
    return next_prime(n)


NOTES = """ENROLMENT STORE - INCIDENT 4471 - PARTIAL TEMPLATE DUMP

The template store keeps one enrolment key per visitor. Keys are never written
to disk in the clear. Each key is sealed under the store's own parameters and
the sealed value is only ever published as a reconciliation sample.

What the dump contains is the sample set: several (mask, sealed) pairs per
visitor, shuffled across candidates. Per the store's assessment, a sample set
is enough to reconcile a key against an enrolment you already hold, and
useless against one you do not.

VISITOR-00 has an open access dispute on the third floor and their template
was exported for the review. The review copy is the one with the finding in it.

The store's own notes, from whoever wrote them:

  - The modulus is published once per store, under "moduli", and each row
    carries the index of the one it was sealed under.
  - The parameters the store seals against are in the store's source. You do
    not have the source.
  - Reconcile a candidate fully before starting the next. A candidate that
    looks right against one pair looks right against every pair, for the wrong
    key too.

The review note for VISITOR-00 is sealed the same way their key was. Recover
the key, unseal the note.
"""


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)
    rng = random.Random(SEED)

    moduli = [random_prime(rng), random_prime(rng)]

    keys = {}
    for i, name in enumerate(NAMES):
        keys[name] = ADMIN_KEY if i == 0 else rng.getrandbits(KEY_BITS)

    rows = []
    for name, key in keys.items():
        mi = rng.randrange(2)
        q = moduli[mi]
        for _ in range(LEAKS_PER_CANDIDATE):
            mask = rng.getrandbits(255) | 1
            err = rng.randrange(-NOISE, NOISE)
            rows.append({
                "candidate": name,
                "modulus": mi,
                "mask": hex(mask),
                "sealed": hex((mask * key + err) % q),
            })
    rng.shuffle(rows)

    store = {
        "store": "eigenface enrolment template store",
        "incident": 4471,
        "moduli": [hex(m) for m in moduli],
        "note": "mask index and modulus index are per-row. Sealing parameters are not published.",
        "rows": rows,
    }

    with open(os.path.join(HANDOUT, "template_store.json"), "w") as f:
        json.dump(store, f, indent=2, sort_keys=True)
        f.write("\n")

    with open(os.path.join(HANDOUT, "enrolment_notes.txt"), "w") as f:
        f.write(NOTES)

    # The sealed review note. Sealed the same way the store seals keys, so the
    # player's own recovered key is the unsealing key.
    note = (
        "REVIEW NOTE - VISITOR-00 - THIRD FLOOR DISPUTE\n\n"
        "Finding: the visitor badge was presented twice inside four minutes, at\n"
        "two doors that are eleven floors apart. Both reads matched the stored\n"
        "template, so the template is not the problem. The badge is.\n\n"
        f"{FLAG}\n\n"
        "Filed under: yes, the key was recoverable from the samples.\n"
    )
    kb = ADMIN_KEY.to_bytes(KEY_BITS // 8, "big")
    sealed = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(note.encode()))
    with open(os.path.join(HANDOUT, "visitor00_note.sealed"), "wb") as f:
        f.write(sealed)

    manifest = [
        "enrolment_notes.txt   what the dump is and what to do with it",
        "template_store.json   moduli and the (mask, sealed) reconciliation samples",
        "visitor00_note.sealed  the VISITOR-00 review note, sealed under their key",
        "",
        "Sealing parameters are not published. The store's assessment is that",
        "they do not need to be.",
        "",
    ]
    with open(os.path.join(HANDOUT, "manifest.txt"), "w") as f:
        f.write("\n".join(manifest))

    # Self-check: the generator's own constants must be consistent with the
    # challenge, so a mistake here fails at build time rather than on the night.
    assert ADMIN_KEY.bit_length() <= KEY_BITS
    assert ADMIN_KEY.bit_length() == KEY_BITS, "the key should sit on the bound"
    assert NOISE < KEY_BOUND, "noise bound must be inside the key width"
    assert len(NAMES) >= 2
    assert FLAG in note
    print("handout written:", os.path.normpath(HANDOUT))


if __name__ == "__main__":
    main()
# et_tu_brute — solution

**Flag:** `cyber_quest{3t_tu_k3ybrut3_b4072a}`
**Difficulty:** medium-hard

## The setup

Memo 77-C arrives in two pieces:

- `memo_cover.txt` — Caesar-shifted. The receiving desk routed it "as
  routine" and, helpfully, documented the two facts that survive sealing:
  1. every memo body opens with the standard header
     `MEMORANDUM ORDINARY ENGINEERING` (a 29-letter crib, in plaintext
     terms), and
  2. the keyphrase is Latin.
- `memo_body.txt` — repeating-key Vigenère, letters-only keyed, case and
  punctuation preserved.

## Stage 1 — the cover (Caesar)

Brute-force all 26 shifts and score with chi-squared against English
frequencies. Shift **11** pops out immediately; the cover reads as the
plain text above.

## Stage 2 — the body (Vigenère, two paths)

**Path A — the crib (intended).** The body's first 29 letters are known:
`MEMORANDUMORDINARYENGINEERING`. Key letter = cipher − plain mod 26 over
those 29 letters gives

```
VENIVIDICIVENIVIDICIVENIVIDIC
```

Then find every length L for which the stream is consistent — i.e.
`stream[i] == stream[:L][i mod L]` for all i. Only **L = 10** (and the
trivial L = 29 repeat of the whole crib) survives, so the keyphrase is
`VENIVIDICI`.

**Path B — the tradition.** The cover says the keyphrase is Latin. Famous
Latin candidates tried directly against the body — `VENIVIDIVICI` (13,
wrong), `CARPEDiem`-style phrases — eventually land on the corrected
*veni, vidi, vici* contraction `VENIVIDICI`, which decrypts cleanly. Slower,
and Legal would call it character-building.

## Stage 3 — read the memo

Decrypting the body with `VENIVIDICI` yields Legal's ruling (and its
opinions about the vault note and the onion from slots 17 and 18). The
flag is at the bottom:

```
Flag: cyber_quest{3t_tu_k3ybrut3_b4072a}
```

## Reference solve

`admin/solve.py` runs all three stages — chi-squared Caesar break, crib
derivation, consistency-checked key-length recovery, decryption.
`admin/verify.sh` regenerates the handout (`deployment/make_memo.py`),
solves a fresh copy, and asserts the flag.

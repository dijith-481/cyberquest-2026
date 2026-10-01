# eigenface — solution

**Flag:** `cyber_quest{3y3_f4c3_m34r_th3_fl4t_fl0w3r}`
**Difficulty:** easy

## The setup

An enrolment store seals one key per visitor and publishes reconciliation
samples. The dump states that the samples are useless without an enrolment you
already hold, and that the sealing parameters are in the store's source.

Four files:

- `template_store.json` — two 256-bit primes, and 24 `(mask, sealed)` samples
  across six candidates. Each row carries the index of the prime it was sealed
  under. All four rows for a candidate share that prime.
- `enrolment_notes.txt` — the store's position, and a warning about trusting a
  single pair.
- `visitor00_note.sealed` — the review note, XOR-sealed under VISITOR-00's key.
- `manifest.txt` — a file index.

## Stage 1 — the direct read fails

Invert a mask and look at what comes out:

```
key = (sealed * mask⁻¹) mod q
```

This is 256 bits wide. It should be a key, so the store is not sealing a plain
product. Something is added before sealing:

```
sealed = (mask * key + e)  mod  q
=>  key = (sealed - e) * mask⁻¹  mod  q
```

Both `key` and `e` are unknown and the equation is one line, so the solve
depends on which one is small enough to enumerate. Try `e` — widen its bound by
doubling until a candidate lands under 2⁶⁴:

```
|e| < 2^10 → nothing
…
|e| < 2^17 → candidates
```

The bound nobody published turns out to be enumerable while the key it protects
is not.

## Stage 2 — recover the key

For each candidate, take one of its four rows, search `e` over ±2¹⁷, and keep
the values that land under 2⁶⁴. Each `e` yields a candidate uniform in `[0, q)`,
so roughly one in 2¹⁹² survives the width test — about 2⁻¹⁷⁴ expected false
positives across the whole 2¹⁸ search. In practice the filter alone pins it:

```
VISITOR-00: 0x9e3779b97f4a7c15
VISITOR-01: 0x910ba5f40cc299f6
VISITOR-02: 0xc0091698b5148840
VISITOR-03: 0x46dce989fff32453
VISITOR-04: 0xeb95e64077893668
VISITOR-05: 0xc1cfdd31de33eaf5
```

`solve.py` still checks each candidate against a second row via the residual
`(sealed - mask*key) mod q`, which must equal that row's own `e`. On this
construction that check can never fail — the numbers above are why. It is
included because it is the right thing to write, and it becomes load-bearing if
the key ever sits closer to the modulus.

## Stage 3 — unseal the note

VISITOR-00's note is XOR against their 8-byte key:

```
kb   = key.to_bytes(8, "big")
note = bytes(b ^ kb[i % 8] for i, b in enumerate(sealed))
```

```
REVIEW NOTE - VISITOR-00 - THIRD FLOOR DISPUTE

Finding: the visitor badge was presented twice inside four minutes, at
two doors that are eleven floors apart. Both reads matched the stored
template, so the template is not the problem. The badge is.

cyber_quest{3y3_f4c3_m34r_th3_fl4t_fl0w3r}
```

## The shortest solve

```
python3 admin/solve.py handout/
```

~1.4s, stdlib only. It derives the width filter and the error bound rather than
assuming them, then unseals the note.

## Alternate approach

Ignore the modulus-sharing structure and take the first candidate per row; six
rows, 6 wins. Or solve only VISITOR-00 — the flag is in its note, and the other
five candidates exist so that "recover the flag" and "find the right person"
cost the same. The manifest's `VISITOR-00` naming is the only pointer to which
note matters.

## Notes on the construction

Not a sound HNP. Real HNP puts the secret at full modulus width and only the
error small, so recovery needs lattice reduction. Here the key is 64 bits *and*
the error is 17, both small — what makes it solvable is the 192-bit gap between
them, not lattice structure.

The handout's closing warning ("a candidate that looks right against one pair
looks right against every pair, for the wrong key too") describes false
positives the construction cannot produce. It is the store talking, and the
store is wrong about its own claim that the samples are unusable.

## What verification establishes

`admin/verify.sh` regenerates the handout (`deployment/make_handout.py`),
hashes the committed copy first so drift fails rather than self-repairs, then
solves a fresh copy with `admin/solve.py` and asserts the flag.

Stage 3b greps every handout file for the sealing relation, the error bound,
either bit width, and terms like `modinv` or `HNP` — the first build published
all of those in the dump's `note` field, which handed over the solve.
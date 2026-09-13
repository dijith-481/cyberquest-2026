# uglified — solution

**Flag:** `cyber_quest{m1n1f13d_n0t_h1dd3n_5d7e1a}`
**Difficulty:** easy

## The setup

The handout is `bundle.js` — the oe-warranty claim validator, shipped
minified and lightly obfuscated — plus a note explaining how to run it:
`node bundle.js <receipt-key>`. Exactly one receipt is honored. A `grep`
for `cyber_quest` finds a retired receipt string in dead code. It is a
decoy — the bundle never accepts it.

## The solve

1. **Run it.** Confirm the oracle: no argument prints usage (exit 1),
   junk prints `claim denied.` (exit 2). The bundle is plain Node, so
   everything it knows is in the file.
2. **Untable the strings.** All readable text lives in one array of
   base64 blobs, rotated at load by a short IIFE
   (`push(shift())` × N). Replicate the rotation: read the array literal
   and the count, rotate forward, base64-decode every entry. Nine entries,
   all short.
3. **Read the check.** Past the hex identifiers it is one function:
   the candidate must start with `cyber_quest{`, end with `}`, and its
   body bytes must satisfy
   `body[i] XOR KEY[i mod 16] XOR ((i*0x1f+0x03) & 0xff) == TARGET[i]`.
   `KEY` decodes to exactly 16 bytes; `TARGET` is the one 20–60 byte
   entry. Nothing else in the table has those lengths.
4. **Invert it.** `body[i] = TARGET[i] XOR KEY[i mod 16] XOR mask(i)`,
   wrap it in `cyber_quest{...}`, and feed it back to the bundle, which
   prints `warranty honored. receipt: ...`.

```bash
$ node bundle.js nope
claim denied.
$ python3 admin/solve.py handout
cyber_quest{m1n1f13d_n0t_h1dd3n_5d7e1a}
$ node bundle.js 'cyber_quest{m1n1f13d_n0t_h1dd3n_5d7e1a}'
warranty honored. receipt: cyber_quest{m1n1f13d_n0t_h1dd3n_5d7e1a}
```

No brute force is needed; the only search is the 9 × 1 table pairing,
and the bundle itself confirms the answer.

## Reference solve

`admin/solve.py` parses the table and rotation count with two regexes,
replicates the runtime rotation, filters entries by decoded length (target
20–60 bytes, key exactly 16), inverts each pair through the mask constants
parsed from the check loop, and submits each well-formed candidate to the
bundle — printing the first one it accepts. `admin/verify.sh` regenerates the
handout deterministically (`deployment/generate.py --seed
oe-uglified-30`), solves a fresh copy, checks accept/reject/usage
behavior, and asserts the real flag is absent from the handout while
the decoy is present.

## Design notes

- The mask constants, table size, and key length are fixed so the solve
  stays readable; seeded rotation, shuffled slot order, and hex
  identifiers make every regenerated variant byte-different.
- The decoy receipt is plaintext in never-called dead code: `grep`
  finds it first, the check never touches it.
- Anti-copy variants: rerun `deployment/generate.py` with a different
  `--seed` (same or new `--flag`); the solve method is unchanged while
  every constant changes.

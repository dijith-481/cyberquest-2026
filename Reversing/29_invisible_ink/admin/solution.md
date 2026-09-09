# invisible_ink — solution

**Flag:** `cyber_quest{wh1t3sp4c3_supply_ch41n_8f3a2c}`
**Difficulty:** medium

## The setup

The handout is a vendored npm-style package, `oe-format` 2.4.1 — fourteen
boring string helpers for the badge-printing pipeline, plus `package.json`
and a note. The source even claims `prettier --check` passes with no
trailing whitespace. That claim is the lie; the file is the challenge.

A `grep` for `cyber_quest` finds one hit immediately: a retired v1 receipt
in a comment. It is a decoy — submitting it fails.

## The solve

1. **Show the invisible.** The file looks clean because editors hide
   trailing whitespace. Run `cat -A index.js` (or `grep -n ' $'`, or turn
   on visible whitespace): nearly every line ends in a tail of spaces and
   tabs, 8–28 characters long. Normal code does not do that.
2. **Read the bits.** Space = 0, tab = 1, MSB first, concatenated in line
   order, chunked into bytes. The bytes are ASCII: a second, hidden JS
   module — the "internal seal" build artifact.
3. **Reverse the seal.** The hidden module holds one base64 blob `D` and a
   version string `V` (`"2.4.1"`, matching `package.json`):
   `flag[i] = D[i] XOR V[i mod len(V)]`. Evaluate it — by reading, or by
   running the module's own `unseal()` under node — and the flag prints.

```bash
$ cat -A index.js | head -5        # tails of ^I and spaces on every line
$ python3 admin/solve.py handout
cyber_quest{wh1t3sp4c3_supply_ch41n_8f3a2c}
$ python3 admin/solve.py --emit-payload handout > seal.js
$ echo 'console.log(unseal());' >> seal.js && node seal.js
cyber_quest{wh1t3sp4c3_supply_ch41n_8f3a2c}
```

## Reference solve

`admin/solve.py` extracts the bits, decodes the module, parses out the
blob and the version key with two regexes, and unseals the flag in pure
Python. `admin/verify.sh` regenerates the handout deterministically
(`deployment/generate.py --seed oe-invisible-ink-29`), solves a fresh
copy, `node --check`s both the visible file and the extracted payload,
runs the payload under node, and asserts the flag — while also asserting
the real flag is absent from the handout and the decoy is present.

## Design notes

- The payload is spread round-robin with a seeded RNG (8–28 bits per
  stop), so every variant has different tails but the same method.
- The XOR key is the package version, tying the three handout files
  together: the key is in plain sight in `package.json`, but only the
  hidden module says it is a key.
- Anti-copy variants: rerun `deployment/generate.py` with a different
  `--seed` (same or new `--flag`); the solve method is unchanged while
  every tail changes.

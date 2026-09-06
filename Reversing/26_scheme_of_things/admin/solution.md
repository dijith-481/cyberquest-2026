# scheme_of_things — solution

**Flag:** `cyber_quest{struktur3_n0t_str1ngs_9c4e7a}`
**Difficulty:** medium

## The setup

`oe-evaluator` is a stripped x86-64 ELF. It prompts for a passphrase and,
on success, prints the flag. `strings` shows Lisp-flavored decoys
(`lambda`, `quote`, `cons`, `car`, `cdr`) and nothing else useful — the
passphrase is not compared as a string and no Scheme source is embedded.

## The solve

1. **Find the blob.** In Ghidra/IDA/radare2, `main` reads a passphrase,
   then walks a static array (`program_blob`) one byte at a time through
   a decoder (`dec_at`): `plain[i] = blob[i] ^ (i*A + B) ^ rol8(i + C, 3)`,
   with `A`, `B`, `C` as `#define`s baked into the binary. That decoded
   stream is the hidden program.

2. **Recover the AST format.** `parse_node` reads one tag byte per node
   and dispatches on four randomized constants (`TAG_INT`, `TAG_BOOL`,
   `TAG_SYM`, `TAG_LIST` — 32-bit ints, 1-byte bools, 16-bit symbol IDs,
   and a count-prefixed list). Decode the blob with the keystream and the
   tags fall out of repeated structure.

3. **Recover the symbol IDs.** The evaluator dispatches on the symbol ID
   of the first element of every list. Tracing the dispatch chain recovers
   the twelve operators: `length`, `char`, `add`, `xor`, `rol8`, `mod`,
   `eq`, `and`, `if`, plus unused noise ops `sub`, `or`, `not`.

4. **Read the hidden expression.** The decoded AST is equivalent to:

   ```scheme
   (and
     (= (length) 20)
     (= (mod (+ (xor (rol8 (char 0) S0) M0) B0) 256) T0)
     ...
     (if #f (= <plausible-but-fake constraint>) #t)
     (if #t #t (= <plausible-but-fake constraint>)))
   ```

   The dead `if` branches are semantic noise — they always evaluate
   truthy and never constrain the input. Shuffled ordering and the
   redundant pairwise `(= (mod (+ (char i) (char j) B) 257) T)` checks
   are noise too.

5. **Invert the per-character constraints.** Each byte is
   `(mod (+ (xor (rol8 c_i) mask) bias) 256) == target`, so:

   ```python
   y = (target - bias) & 0xff
   y ^= mask
   c_i = ror8(y, shift)
   ```

   That reconstructs the 20-byte passphrase directly — the per-character
   math is deliberately invertible; the reversing is the challenge.

6. **Type it in.** `main` computes `FNV-1a(passphrase) ^ salt`, advances
   a xorshift64* state, and XORs the flag cipher byte-per-byte with the
   high byte of each step. The correct passphrase is the key; the flag
   never exists as plaintext in the binary, so patching the success
   conditional or `reveal` gets you nowhere without it.

```
$ echo 'structure_not_syntax' | ./evaluator
oe-evaluator // calibration build
The evaluator does not ask what you typed. It asks what the expression becomes.
passphrase> cyber_quest{struktur3_n0t_str1ngs_9c4e7a}
```

## Reference solve

`admin/solve_reference.py` reconstructs the passphrase from
`deployment/organizer/metadata.json`.
`admin/verify.sh` regenerates a fresh instance (`deployment/generate.py`,
deterministic from `--seed oe-scheme-of-things-26`), solves it, and
asserts the flag. The generator also self-tests positive and negative
paths at build time.

## Design notes

- Noise is semantic, not adversarial: decoy strings, unused operators,
  dead branches, shuffled constraints, randomized tags/symbol IDs. No
  anti-debugging, ptrace tricks, or opaque virtualization.
- Anti-copy variants: regenerate with a different `--seed`; the solve
  method stays identical while every constant, tag, ID, and the flag
  salt change.

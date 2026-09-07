# scheme_of_things — solution

**Flag:** `cyber_quest{ch41n3d_b4cktr4ck1ng_9d41f3}`
**Difficulty:** medium

## The setup

`oe-evaluator` is a stripped x86-64 ELF. It prompts for a "passphrase"
but the kiosk note and the binary itself say it expects *a statement in
the approved grammar*. `strings` shows Lisp-flavored decoys (`lambda`,
`quote`, `cons`) and nothing else useful — the answer is never compared
as a string and no source ships with the handout.

## The solve

1. **Recover the input grammar.** In Ghidra/IDA/radare2, `main` runs a
   recursive-descent parser before anything else: parens, symbols
   `[a-z0-9_-]`, decimal integers, whitespace — a tiny s-expression
   grammar. It rejects unbalanced parens, stray characters, and
   non-expression input outright, so the answer must *parse*, not just
   satisfy math. The parser also records the grammar facts the hidden
   program checks: input byte length `(length)`, nesting `(depth)`, and
   atom count `(width)`.

2. **Recover the opcode table.** The evaluator hashes every operator
   name at *runtime*: `op_id = h16(name)`, where
   `h16 = fnv1a64("oe:<variant>:<domain>:<name>") & 0xffff`. The domain
   string (`oe:2:op`) is visible in the binary, so once the blob is
   decoded the symbol IDs map straight to operators — no input
   knowledge required. The dispatch chain itself (`add` does sums,
   `rol8` rotates, `mul` multiplies, `div` truncates, `band` masks)
   confirms the mapping, and the two plausible-but-unused ops (`sub`,
   `lnot`) are noise.

3. **Decode the hidden program.** `parse_node` walks a static blob one
   byte at a time through `plain[i] = blob[i] ^ (i*A + B) ^ rol8(i + C, 3)`
   and dispatches on four randomized node tags: int (32-bit), bool,
   symbol (16-bit ID), list (count-prefixed). Decoding yields a real
   AST:

   ```scheme
   (land (= (length) 34) (= (depth) 1) (= (width) 6)
     (let ((s0 153)
           (s1 (mod (add (mul s0 255) (char 0)) 256))
           (s2 (mod (add (mul s1 151) (char 1)) 256))
           (s3 (xor (rol8 s2 1) (char 2)))
           ...)
       (land (= (xor (char 0) 42) 2)                        ;; unique pin
             (= (mod (add (char 1) 145) 257) 244)            ;; unique pin
             (= (mod (mul (char 5) 2) 256) 198)              ;; weak pin: 2 candidates
             ...
             (if #f (= (xor (char 9) 77) 12) #t)             ;; dead decoy: prunable
             (if (eq (band s17 7) 3)                         ;; live decoy: both
                 (eq (char 22) 50) #t)                       ;;   branches true
             (= s34 197))))
   ```

   A `let` special form binds the state chain sequentially — every
   binding reads all previous ones, so the bytes are *coupled*: nothing
   solves independently, and the chain is anchored at both ends
   (`s0` = constant, `s34` = constant).

4. **Model the constraint system.** Almost every byte carries a unique
   pin (affine mod 257 / xor — one candidate each). Just three bytes
   carry *weak* pins (`mul` by 2 mod 256, a single-zero-bit `band`
   mask — two candidates each), each resolved by an adjacent pair-sum
   checksum `(mod (+ (char i) (char j) B) 257) == T`, plus scattered
   state checks `(band s_k M) == V`, plus the final anchor. Most
   decoys are classic dead branches (`(if #f fake #t)`,
   `(if #t #t fake)`) — prunable the moment you notice the literal
   condition. Two are live: they read real state/byte values with both
   branches true, so a wrong candidate that flips one's condition
   falls into a consequence that fails.

5. **Short backtracking DFS.** Forward from `s0`: each byte's candidate
   set comes from its pin (1 value almost everywhere, 2 at the three
   weak spots); the chain step advances the state; state checks prune
   at their index; each adjacent pair checksum resolves its weak pin
   as soon as the later byte is assigned. The search is tiny
   (37 nodes here): 31 bytes solve outright, 3 need one local
   disambiguation each. The result is unique:

   ```
   (chain the state and backtrack 26)
   ```

6. **Cash it in.** `main` computes `FNV-1a(input) ^ salt`, advances a
   xorshift64* state, and XORs the flag cipher byte-per-byte. The flag
   never exists in plaintext, and it is keyed on the *exact* input —
   any alternate accepting statement (there isn't one, per the DFS)
   would decrypt to garbage. Patching the success branch is useless.

```
$ printf '(chain the state and backtrack 26)\n' | ./evaluator
oe-evaluator // calibration build
The evaluator does not ask what you typed. It asks what the expression becomes.
passphrase> cyber_quest{ch41n3d_b4cktr4ck1ng_9d41f3}
```

## Reference solve

`admin/solve_reference.py` runs the same backtracking DFS from
`deployment/organizer/metadata.json` (no answers embedded) and asserts
exactly one solution. `admin/verify.sh` regenerates a fresh instance
(`deployment/generate.py`, deterministic from
`--seed oe-scheme-of-things-26`), confirms the committed handout is
byte-identical, solves it, exercises the binary, and asserts the flag.
The generator additionally self-tests: wrong input, weak-bit mutants,
unbalanced parens, non-expression input, and bad charset input must all
be rejected.

## Design notes

- Noise is semantic, not adversarial: decoy strings, unused operators
  (`sub`, `lnot`), randomized node tags, mostly-dead decoy branches,
  static per-seed opcode IDs. No anti-debugging, ptrace tricks, or
  opaque virtualization.
- Pair *sums* mod 257 are used for cross-byte coupling rather than
  products: a pair product mod 256 is heavily non-injective in two
  variables and would leave hundreds of surviving solutions; sums keep
  the solution unique while still forcing joint reasoning.
- Anti-copy variants: regenerate with a different `--seed`; the variant
  loop re-derives tags, chain forms, pins, pairs, decoys, and the flag
  salt until the puzzle is again uniquely solvable. The solve method is
  unchanged, so variants stay fair.

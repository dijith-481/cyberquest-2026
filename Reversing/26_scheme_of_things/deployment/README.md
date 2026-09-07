# scheme_of_things — deployment

H0 handout challenge: no server. Players download `handout/26_scheme_of_things.zip`
(stripped `oe-evaluator` ELF + note) and run it locally.

## Regenerate everything

```bash
python3 generate.py --seed oe-scheme-of-things-26 \
  --password '(chain the state and backtrack 26)' \
  --flag 'cyber_quest{ch41n3d_b4cktr4ck1ng_9d41f3}' \
  --out build
```

Requires Python 3.10+ and GCC (or `--no-build` on a machine without it).
Deterministic: the same seed reproduces the committed `handout/` bytes
exactly (checked by `admin/verify.sh`).

The passphrase must itself be a valid s-expression in the evaluator's
grammar (parens, `[a-z0-9_-]` symbols, integers). Generator output:

```text
build/
├── player/                  # distributables → handout/
│   ├── evaluator
│   └── README.txt
├── organizer/               # seed data → deployment/organizer/
│   ├── challenge.c
│   ├── Makefile
│   ├── metadata.json        # puzzle constants, tags, encoding, flag salt/cipher
│   └── solve_reference.py   # → admin/solve_reference.py
└── 26_scheme_of_things.zip  # the player bundle
```

## Design summary (v2.1 — softened to medium)

- **Input drives the parse.** The passphrase is parsed by a real
  recursive-descent s-expression grammar before anything else runs;
  `(length)`, `(depth)`, and `(width)` are constraints in the hidden
  program.
- **Static opcode IDs.** `op_id = h16(name)` per seed — once the blob
  is decoded, the visible domain string maps IDs straight to operators.
- **Coupled unknowns, simple steps.** A `let`-bound state chain
  `s0..sN` (anchored at both ends) makes every byte depend on all
  previous ones, but each step is a simple bijective mix
  (rol/xor, odd-mul/add).
- **Mostly unique pins.** ~31 of 34 bytes solve outright (affine mod
  257 / xor pins); 2–6 weak pins (`mul` by 2 mod 256, single-zero-bit
  `band` masks, `div` by 2) leave 2 candidates each, resolved by
  adjacent pair-sum checksums mod 257 — a short DFS (certified unique
  by the generator's reference solver).
- **Mostly dead decoys.** Classic `(if #f fake #t)` / `(if #t #t fake)`
  branches prune by inspection, plus two live ones reading real
  input-dependent values.
- **Sealed flag.** Stream-XOR behind `FNV-1a(input) ^ salt`; no plaintext
  flag in the binary, patching the success branch is useless.

Noise is semantic (decoy strings, unused operators, randomized node
tags), never anti-debugging. The generator self-tests positive,
negative, weak-bit-mutant, and grammar-violation paths at build time.

## Anti-copy variants

Regenerate per team with a different `--seed`. The internal variant loop
(`seed#0`, `seed#1`, …) re-derives node tags, chain forms, pins, pairs,
decoys, and the flag salt until the puzzle is again uniquely solvable;
the solve method is unchanged, so variants stay fair.

# scheme_of_things — deployment

H0 handout challenge: no server. Players download `handout/26_scheme_of_things.zip`
(stripped `oe-evaluator` ELF + note) and run it locally.

## Regenerate everything

```bash
python3 generate.py --seed oe-scheme-of-things-26 \
  --password 'structure_not_syntax' \
  --flag 'cyber_quest{struktur3_n0t_str1ngs_9c4e7a}' \
  --out build
```

Requires Python 3.10+ and GCC (or `--no-build` on a machine without it).
Deterministic: the same seed reproduces the committed `handout/` bytes
exactly (checked by `admin/verify.sh`).

Generator output:

```text
build/
├── player/                  # distributables → handout/
│   ├── evaluator
│   └── README.txt
├── organizer/               # seed data → deployment/organizer/
│   ├── challenge.c
│   ├── Makefile
│   ├── metadata.json        # tags, symbol IDs, constraints, flag salt/cipher
│   └── solve_reference.py   # → admin/solve_reference.py
└── 26_scheme_of_things.zip  # the player bundle
```

## Anti-copy variants

Regenerate per team with a different `--seed` (same password and flag).
The seed changes node tags, symbol IDs, AST ordering, dead branches,
constraint constants, blob encoding, and the flag salt; the solve method
is unchanged, so variants stay fair.

## Design summary

Stripped ELF evaluating a serialized Scheme-like AST (int/bool/sym/list
nodes) decoded byte-at-a-time from `.rodata`. The passphrase satisfies
per-character `rol8/xor/add/mod` constraints plus dead `if` branches and
unused operators as semantic noise. The flag is stream-XOR sealed with
FNV-1a(passphrase) ^ salt and only decrypts after the hidden expression
accepts the input — no plaintext flag, patching the success branch
doesn't help. Medium difficulty: `-O1 -fno-inline`, stripped, encoded
blob, randomized operator IDs.

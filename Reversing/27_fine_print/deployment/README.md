# fine_print — deployment

H0 handout challenge: no server. Players download `27_fine_print.zip`
(stripped `licenseguard` ELF + note) and work locally.

## Regenerate everything

```bash
python3 deployment/generate.py --seed oe-fine-print-27
```

Requires Python 3.10+ and GCC (or `--no-build` on a machine without it).
Fragments are deterministic from the seed; the ELF itself rebuilds with
whatever toolchain is present but always stays solvable (checked by
`admin/verify.sh`).

Generator output:

```text
handout/
├── licenseguard   # stripped ELF players receive
└── README.txt     # player note
deployment/organizer/
├── challenge.c    # generated source (fragments baked in)
└── Makefile       # `make` rebuilds the binary into handout/
```

## Anti-copy variants

Regenerate with a different `--seed` (same or new `--flag`). The seed
changes every fragment; the solve method (strings → length tell → XOR)
is unchanged, so variants stay fair.

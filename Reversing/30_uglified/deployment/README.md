# uglified — deployment

H0 handout challenge: no server. Players download `30_uglified.zip`
(`bundle.js` + `NOTE.txt`) and work locally with node.

## Regenerate everything

```bash
python3 deployment/generate.py --seed oe-uglified-30
```

Requires Python 3.10+ and node on PATH (the generator self-tests the
bundle: accepts the flag, rejects junk, prints usage with no argument).
Identifiers, slot order, rotation count, and key material are
deterministic from the seed.

Generator output:

```text
handout/
├── bundle.js   # obfuscated validator players receive
└── NOTE.txt    # player note (how to run it)
deployment/organizer/
└── claim.js    # clean reference source (logic only, placeholders)
```

## Anti-copy variants

Regenerate with a different `--seed` (same or new `--flag`). The seed
changes the key, the target, the table order, the rotation, and every
identifier; the solve method (untable → read the check → invert) is
unchanged, so variants stay fair.

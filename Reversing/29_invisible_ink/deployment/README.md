# invisible_ink — deployment

H0 handout challenge: no server. Players download `29_invisible_ink.zip`
(`index.js` + `package.json` + `NOTE.txt`) and work locally.

## Regenerate everything

```bash
python3 deployment/generate.py --seed oe-invisible-ink-29
```

Requires only Python 3.10+. The payload tails are deterministic from the
seed; the visible source is fixed.

Generator output:

```text
handout/
├── index.js       # visible helpers + trailing-whitespace payload
├── package.json   # the pin (version doubles as the seal key)
└── NOTE.txt       # player note
deployment/organizer/
├── index.visible.js  # visible source before the payload is spread
└── payload.js        # hidden seal module (decoded form)
```

## Anti-copy variants

Regenerate with a different `--seed` (same or new `--flag`, optional
`--version`). The seed changes every tail; the solve method (tails →
bits → module → version-XOR) is unchanged, so variants stay fair.

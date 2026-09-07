# fine_print — solution

**Flag:** `cyber_quest{x0r_a11_th3_str1ngs_2gether_3f8a1d}`
**Difficulty:** easy

## The setup

The handout is a single stripped ELF, `licenseguard` — Ordinary
Engineering's license checker. Running it normally never leaks the flag:
`./licenseguard <anything>` only prints `Access denied…` (or the usage /
length error). The `check_fake_license()` function is a red herring; it
folds one fragment together with the user input into a single byte that
essentially never equals `0x42`, and it never combines or prints the real
key material.

## The solve

1. **Run `strings`.** Most output is obvious noise: usage text, error
   messages, a fake license path, compiler version strings, libc symbols,
   section names.
2. **Spot the tell.** Exactly four lines are all the same length (47
   characters here — the flag length) of random-looking punctuation and
   letters, unlike anything else in the binary. No decoy shares that
   length, which is what makes "XOR them all together" well-defined.
3. **XOR them byte-by-byte** (same position across all four fragments).
   The flag falls out in plaintext:

```python
frag = [s.encode() for s in cands]  # the four 47-char lines
flag = bytes(f1[i] ^ f2[i] ^ f3[i] ^ f4[i] for i in range(47))
```

```
$ strings licenseguard | awk '{ print length, $0 }' | sort -n | tail
...
$ python3 admin/solve.py handout
cyber_quest{x0r_a11_th3_str1ngs_2gether_3f8a1d}
```

## Reference solve

`admin/solve.py` reimplements `strings` in pure Python (runs of
printable ASCII ≥ 4 bytes), keeps the lines whose length equals the
known tell length, XORs them, and prints the result. `admin/verify.sh`
regenerates the handout deterministically
(`deployment/generate.py --seed oe-fine-print-27`), solves a fresh copy,
and asserts the flag — proving the challenge ships in a solvable state.

## Design notes

- All four fragments are the same length as the flag, printable,
  spaceless, and free of `"` / `\` so they sit cleanly as C string
  literals and survive `strings` as single tokens.
- Fragments are derived per byte position (N−1 random alphabet bytes,
  last byte solved), so the committed values are uniform over the safe
  alphabet conditioned on XOR-ing to the flag.
- The binary is stripped so debug/local symbol noise does not crowd the
  `strings` output further.
- Anti-copy variants: rerun `deployment/generate.py` with a different
  `--seed` (and optionally `--flag`); the solve method is unchanged while
  every fragment changes.

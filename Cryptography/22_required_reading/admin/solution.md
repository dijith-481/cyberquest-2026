# required_reading — solution

**Flag:** `cyber_quest{r34d_th3_h4ndb00k_c0v3r_t0_c0v3r_2b8d0e}`
**Difficulty:** easy

## The setup

HR seals the orientation note against the employee handbook itself:

- `handbook.txt` — the employee handbook, revision 7. The key.
- `cover_memo.txt` — the memo describing the method, deadpan: each
  number is a zero-based byte offset into `handbook.txt`.
- `orientation_note.enc` — 470 integers, twelve per line.

## The solve

There is no second layer. The memo is telling the truth: byte `n` of
the note is byte `n`-at-`handbook.txt`, i.e.:

```python
book = open("handbook.txt", "rb").read()
note = b"".join(book[int(n):int(n) + 1]
                for n in open("orientation_note.enc").read().split())
```

The decoded note is a welcome message, a starter gift, and:

```
Flag: cyber_quest{r34d_th3_h4ndb00k_c0v3r_t0_c0v3r_2b8d0e}
```

The one judgment call is the indexing convention — zero-based bytes,
not one-based, not lines, not words. The memo states it outright, and
the first decoded bytes (`ORIENTATION NOTE`) confirm it immediately:
if the convention were wrong, the output would be shifted garbage
instead of clean prose, so the check costs one attempt.

## Reference solve

`admin/solve.py` indexes the book and prints the note.
`admin/verify.sh` regenerates the handout (`deployment/make_handout.py`),
solves a fresh copy, and asserts the flag.

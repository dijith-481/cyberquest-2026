# onion_pattern — solution

**Flag:** `cyber_quest{p33l_p4t13ntly_4ll_th3_w4y_d0wn_5e2b19}`
**Difficulty:** medium-hard

## The setup

`onion.txt` is a 23,840-character hex blob. The challenge never says how
many layers; the ticket said "several steps deep." Every layer beneath the
surface is a JSON envelope:

```json
{
  "onion": "asset-transfer-pipeline",
  "layer": 8,
  "of": 8,
  "op": "base64",
  "hint": "Transport wrapper: Base64. ...",
  "data": "..."
}
```

`op` names how `data` was encoded; `hint` is deadpan documentation — and,
critically, for the XOR layers the **key only exists inside the hint**. You
cannot script your way past a seal you didn't stop to read.

## The peel (9 hops, outside in)

| hop | op         | detail                                        |
| --- | ---------- | --------------------------------------------- |
| 0   | hex        | the file itself (the "file format" layer)     |
| 1   | base64     | transport wrapper                             |
| 2   | ascii85    | plain a85, no adobe brackets                  |
| 3   | mirror     | the whole JSON string is reversed             |
| 4   | base32     | A–Z, 2–7                                      |
| 5   | xor-hex    | hex-decode, XOR with `p34r1` (from the hint)  |
| 6   | rot13      | letters only                                  |
| 7   | base64     | again                                         |
| 8   | xor-hex    | hex-decode, XOR with `0n10n` (from the hint)  |
| —   | core       | `{"pattern": ..., "note": ...}`               |

Practical notes for a manual peel:

- `CyberChef` handles the whole chain with "From Hex" → magic or by chaining
  the named ops; the two XOR ops use "From Hex" + "XOR" with the key typed
  as UTF-8.
- `base64 -d`, `base32 -d`, and `python3 -c` one-liners also do it; the only
  genuinely fiddly hop is ascii85 — Python's `base64.a85decode` (plain
  flavor, no `<~ ~>`) matches the hint.
- The mirror hop reverses *characters*, not bytes, so `tac`/`rev` on the
  file will not work — you reverse the decoded string.

The core payload:

```
FLAG: cyber_quest{p33l_p4t13ntly_4ll_th3_w4y_d0wn_5e2b19}
```

## Reference solve

`admin/solve.py` peels generically — it reads each envelope's `op`, applies
the inverse, and scrapes the XOR key out of the hint, so it never hardcodes
the chain. `admin/verify.sh` regenerates `onion.txt`
(`deployment/make_onion.py`), solves a fresh copy, and asserts the flag.

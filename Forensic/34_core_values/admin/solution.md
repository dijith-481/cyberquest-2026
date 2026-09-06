# core_values — solution

**Flag:** `cyber_quest{v4lu3s_4rr1v3_0ut_0f_0rd3r_k33p_th3_s3q_b3f19}`
**Difficulty:** medium-hard

## The setup

The handout is one file: `valuesd_heap.raw`, a raw snapshot of the crashed
process's `[heap]` mapping. `strings` shows the app was thinking out loud
about printers, desk plants, and a "quarterly values sync" — but no flag:

```bash
strings valuesd_heap.raw | grep -i cyber     # nothing
```

That absence is the point. The crash report, which `strings` *does* surface,
explains why:

> the values ledger is an array of 16-byte records. bytes 0-3: record tag
> (LEDJ = live record, AUDT = audited/retired). bytes 8-11: sequence number
> (uint32, this is a memory dump so it is little-endian here). byte 12: the
> value byte. … records are stored in wall-clock order, which is not
> sequence order …

and the audit note adds: the message was written into the ledger **one byte
per LEDJ record, in sequence order, starting at 1**; AUDT records are
retired values; LEDJ records with a sequence above 100 are writer scratches.

## Step 1 — find the ledger

The heap is ~150 KB of libc noise, and the strings are separate from the
ledger. Scan for a run of adjacent 16-byte records whose tag bytes are
`LEDJ` or `AUDT` — the ledger is one solid block (~80 records once the
writer's scratch copy and the live copy are both counted):

```python
data = open("valuesd_heap.raw", "rb").read()
for off in range(0, len(data) - 16, 4):
    if data[off:off+4] in (b"LEDJ", b"AUDT"):
        # confirm a long run of valid records at stride 16
        ...
```

## Step 2 — read the ledger the way the crash report says

For each 16-byte record:

| offset | meaning                                        |
| ------ | ---------------------------------------------- |
| 0–3    | tag: `LEDJ` (live) or `AUDT` (retired)         |
| 8–11   | sequence number, little-endian in the dump     |
| 12     | the value byte                                 |

Keep only `LEDJ` records with `1 <= seq <= 100`, sort by sequence, take byte
12 of each:

```python
live = {}
for i in range(count):
    rec = data[start + i*16 : start + (i+1)*16]
    tag, seq, val = rec[0:4], int.from_bytes(rec[8:12], "little"), rec[12]
    if tag == b"LEDJ" and 1 <= seq <= 100:
        live[seq] = val
flag = bytes(live[s] for s in sorted(live)).decode()
```

The shuffle matters: memory order is not sequence order (the writer reversed
pairs), so reading the ledger top to bottom produces garbage — this is the
"hard" part of medium-hard.

## Result

```
cyber_quest{v4lu3s_4rr1v3_0ut_0f_0rd3r_k33p_th3_s3q_b3f19}
```

## Step 3 — submit

The missing slide has been restored. The deck is now 40% longer and no more
informative.

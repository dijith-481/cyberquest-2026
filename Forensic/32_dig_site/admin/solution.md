# dig_site — solution

**Flag:** `cyber_quest{g1t_fck_r3m3mb3rs_wh4t_br4nch3s_f0rg3t_d64b02}`
**Difficulty:** medium

## The setup

`skills_archive/` is a real git repository. The visible history is 26 commits,
every one dated 1984–1989 — the broken import backdated everything, so date
sorting is useless. The reflogs were lost in the export. `git log --all` shows
nothing interesting, and **no dangling commit contains the flag**. That is the
trap: the easy `git fsck` win is a decoy layer.

## Step 1 — fsck, and read past the decoys

```bash
git fsck
```

Two dangling candidate imports are decoys: one dangles a "recovery phrase
that was retired by legal," one contains an ASCII drawing of an actual flag.
The third one matters — it commits `cold_storage_receipt.txt`:

```
cold storage receipt — export 1989-47

shipped:        .git/objects/pack/pack-c0c4…ca.pack
not shipped:    .git/objects/pack/pack-c0c4…ca.idx
contents:       skills/spreadsheet_divination.md, calibration included …
```

## Step 2 — git is ignoring an entire pack

```bash
ls .git/objects/pack/
# pack-c0c4….pack        <- and NO pack-c0c4….idx
```

A pack without its index is invisible to git: not in `git log --all`, not in
`git fsck`'s object list, not in `git cat-file`. Revive it yourself:

```bash
git index-pack .git/objects/pack/pack-c0c4….pack
```

Now `git fsck --unreachable` lists a previously invisible import history:
`cold: import spreadsheet divination (stub)` → `cold: calibrate`.

## Step 3 — the pack forgot a blob

```bash
git ls-tree -r <cold-tip> -- skills/spreadsheet_divination.md
# 100644 blob 782ec89… spreadsheet_divination.md

git cat-file -p 782ec89…
# error: unable to unpack 782ec89… header
```

The tree references the file; the pack does not contain it (the calibration
blob was never packed — the receipt even warns it was "handled firmly").

## Step 4 — the damaged loose object

The blob does exist as a loose object at `.git/objects/78/2ec89…`, but its
zlib stream is missing the 2-byte header, so git refuses it. The deflated
payload is intact — inflate it as a **raw** deflate stream:

```python
import zlib
raw = open(".git/objects/78/2ec894777307fe3f66836f6c53b4d20f8b7b83", "rb").read()
print(zlib.decompressobj(-15).decompress(raw).decode())
```

(The equally valid hack: prepend `78 9c` and `zlib.decompress` normally, or
`openssl zlib -d`.)

```
…calibration phrase: cyber_quest{g1t_fck_r3m3mb3rs_wh4t_br4nch3s_f0rg3t_d64b02}
```

## Step 5 — submit

The archive is whole again, in the sense that the flag is out. Housekeeping
remains on the backlog.

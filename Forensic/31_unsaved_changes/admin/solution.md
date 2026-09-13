# unsaved_changes — solution

**Flag:** `cyber_quest{uns4ved_n0t3s_r3m3mb3r_3v3ryth1ng_5a91c4}`
**Difficulty:** easy

## The setup

The handout has three files:

- `standup_notes.md` — the notes as finally saved. Clean. Read it anyway; the
  printer line's rewording history is the tell that the file has an editor
  past.
- `.standup_notes.md.swp` — a vim swap file, snapshotted **mid-incident** (the
  laptop's editor died with the flagged buffer live). The header says the
  session belonged to `k.okafor` on host `lt-oe0442`.
- `.standup_notes.md.un~` — vim's persistent undo file, holding the full
  history of every write.

## Step 1 — the crude route: strings, then a decode

Swap files store buffer text in blocks; undo files store the text of past
states. Neither is encrypted. But QA *pre-hexed* the flag before pasting it
("so the mail keyword alerts miss it" — their words), so `strings` shows a
long lowercase hex run, not a flag:

```bash
strings .standup_notes.md.swp | grep -E '[0-9a-f]{40}'
```

```
63796265725f71...
```

One decode:

```bash
echo 6379626572... | xxd -r -p
```

## Step 2 — the intended route: let vim replay the history

Drop the artifacts in a directory and open the notes:

```bash
vim -u NONE standup_notes.md
:set undofile undodir=.
:rundo .standup_notes.md.un~
:earlier 1f
```

`:earlier 1f` steps back one *file write*. The last write was the cover-up
(deletion of four lines); stepping back one write lands on the flagged draft:

```
* qa found the badge flag. pasting it here as hex so the mail keyword alerts miss it:
* 63796265725f71...
* (that is hex. decode it before the deck. do NOT put this in the all-hands deck.)
* (kevin: this is exactly why we do not have nice things)
```

```python
bytes.fromhex("6379626572...")
# cyber_quest{uns4ved_n0t3s_r3m3mb3r_3v3ryth1ng_5a91c4}
```

Equivalent routes: copy the swap to the swap name vim expects and run
`vim -r standup_notes.md` to recover the crashed session, or `:undolist` /
`:undo 2` to walk the tree by hand.

## Step 3 — submit

Kevin has been informed. Kevin has opinions about hex.

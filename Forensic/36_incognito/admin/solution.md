# incognito — solution

**Flag:** `cyber_quest{1nc0gn1t0_l34v3s_th3_w4l_b3h1nd_9f4c2e}`
**Difficulty:** easy

## The setup

The handout is the wiped laptop's browser profile plus IT's wipe report:

```
it_wipe_report.txt
profile/
  History            (SQLite — the browser history database)
  History-wal        (the write-ahead log, "not checkpointed")
  Bookmarks
  Cache/f_000001..3  (the disk cache, "not managed" by the wipe tool)
```

The report is the roadmap: the wipe tool cleared history rows and "does not
manage the disk cache folder"; the browser was killed mid-write so the WAL
"was not checkpointed."

## Step 1 — confirm the wipe looks real

```bash
sqlite3 profile/History 'select count(*) from urls;'        # 12 clean rows
sqlite3 profile/History "select url from urls where url like '%cyber%';"   # 0 rows
```

The database itself is clean. A player who stops here submits nothing.

## Step 2 — the WAL never forgot

SQLite's WAL holds whole page images. The pre-deletion pages — the ones
containing the flagged history row — are still in `History-wal` as dead
bytes; newer frames supersede them logically, but nothing erased them
physically. Carve, don't query:

```bash
strings profile/History-wal | grep cyber
```

```
https://notes.oe.internal/u/k.okafor/badge-ceremony-2026?k=cyber_quest{1nc0gn1t0_l34v3s_th3_w4l_b3h1nd_9f4c2e}
```

(For a more surgical route: the WAL frame header is a 24-byte record per
page — parse the frames, diff page images, and watch the `urls` rows vanish
between frames. `strings` gets the same answer with less dignity.)

## Step 3 — the cache was never in scope

The wipe report's own excuse — "the tool does not manage the disk cache
folder" — is the second path. The cached copy of the early-access page the
deleted history row pointed at is sitting in `profile/Cache/f_000002`:

```bash
strings profile/Cache/f_000002 | grep cyber
```

```
<!-- the invite key doubles as the ceremony flag for the badge reader:
     cyber_quest{1nc0gn1t0_l34v3s_th3_w4l_b3h1nd_9f4c2e} -->
```

Two artifacts, same flag — the cache corroborates the WAL (or spoils it,
depending on which the player finds first; the story holds up either way).

## Step 4 — submit

The ticket has been reopened. The ticket has been re-closed.

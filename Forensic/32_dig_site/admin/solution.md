# dig_site — solution

**Flag:** `cyber_quest{g1t_fck_r3m3mb3rs_wh4t_br4nch3s_f0rg3t_d64b02}`
**Difficulty:** medium-hard

## The setup

`skills_archive/` is a real git repository. The visible history is 26 commits,
every one of them dated 1984–1989 — the broken import backdated everything, so
**date sorting is useless**: `git log --since`/`--until` windows, "oldest
commit" heuristics, and timeline tools all return the entire repo at once.
That is the trap. The interesting objects are not on any branch.

## Step 1 — notice what is missing

`git branch -a` shows `main` and a stale `archive-import`. `git reflog` is
empty — the export lost the reflogs (the README hints housekeeping never ran).
An empty reflog on a repo with this much history means the export is not
everything that was on the disk.

## Step 2 — ask fsck what the branches forgot

```bash
cd skills_archive
git fsck --lost-found
```

```
dangling commit 06cc2b70...
dangling commit 609e6997...
dangling commit 8929d9fc...
```

Three candidate imports never reached a branch. (If a player's copy *does*
have reflogs, `git fsck --no-reflogs` gives the same answer; `git log --all`
does not — the dangling commits are invisible there.)

## Step 3 — separate the real one from the decoys

Two of the three are decoys, engineered for people who grep first and read
later: one dangles a "recovery phrase that was retired by legal" and one
contains an ASCII drawing of an actual flag. The real one has the most boring
possible shape:

```bash
git show 609e6997 --stat      # "rebase cleanup"
git show 609e6997:skills/spreadsheet_divination.md
```

> Reads future revenue in the cell borders of the Q3 workbook. Calibration
> phrase: **cyber_quest{g1t_fck_r3m3mb3rs_wh4t_br4nch3s_f0rg3t_d64b02}**

The commit message says nothing, the file sits among twenty-five identical
skill files, and the flag is mid-prose — which is why the decoys scream
"pick me."

Alternate route: `git cat-file --batch-all-objects --batch-check` lists every
object in the repo regardless of reachability; walk the commits from there.

## Step 4 — submit

The vendor has been notified. The vendor has sent a survey about the support
experience.

# Emojinated — solution

**Flag:** `cyber_quest{3m0t1c0ns_w4llb04rd_b7ae2865}`
**Difficulty:** easy-medium

## The setup

`wallboard.emoji` is a monoalphabetic substitution of an ordinary
tkinter script: every character except newline became one emoji, via a
fixed seeded shuffle. Newlines survived, so line lengths, indentation
and blank lines are all visible. `note.txt` hands over two cribs: SPACE
and the first line verbatim (`import tkinter as tk`).

## Step 1 — seed the map

Transcribe line 1 against `import tkinter as tk`. That pins 12 symbols
immediately (`i,m,p,o,r,t,space,k,n,e,a,s`), and the note confirms which
emoji is the space. Frequency does the rest of the orientation: the
space emoji is by far the most common, newlines delimit tokens, and the
short-line / indent shapes already look like code.

## Step 2 — drag tkinter cribs

The file is a tkinter script (line 1 says so), so the vocabulary is
small and guessable: `root`, `canvas`, `tk.Tk()`, `title`, `geometry`,
`configure`, `create_text`, `mainloop`, `True`, plus the usual call
shapes `root.title(`, `tk.Canvas(`, `text=FLAG`, `expand=True`,
`highlightthickness=0`. Each guess is placed only where it fits the
known mappings, and only kept when exactly one placement on the line is
consistent — standard crib-dragging, anchored so early guesses cannot
poison the map. Boilerplate values fall out the same way: `"both"`,
`"bold"`, `"Courier"`, `("Courier", 34, "bold")`, `width=900`,
`height=260`, the comment `rev 1957`, geometry `"900x260"` against
`width=`/`height=`, and colors `"#080c14"` / `"#39ff88"` as 7-char
quoted tokens sharing a `#`.

## Step 3 — the FLAG line

One line matches the public wrapper with zero ambiguity:

```
FLAG = "cyber_quest{" ... "}"
```

Every CTF flag here starts with `cyber_quest{`, so the braces, the
`FLAG = "` prefix and the `cyber_quest` literal pin two dozen symbols
at once. The body is `[a-z0-9_]+`, and the generator guarantees every
body character also occurs outside the flag string, so nothing in the
flag is unrecoverable.

## Step 4 — finish and verify

Whatever is left (here: a single emoji) is brute-forced over a small
context-derived pool, keeping the unique assignment under which the
whole file parses (`ast.parse`) and contains a flag. The decoded
`wallboard.py` is ordinary Python — run it and the lobby display draws
the flag.

## Reference solve

`admin/solve.py` automates exactly the path above from the handout
alone (no seed, no key): note cribs, anchored unique-placement drag to
a fixpoint, FLAG-line match, constrained backtracking, `ast.parse`
check. `admin/verify.sh` regenerates the handout deterministically and
re-solves a fresh copy.

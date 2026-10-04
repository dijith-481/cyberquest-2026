# the_corridor_that_remembers — solution

**Flag:** `cyber_quest{f4m1l14r1ty_1s_n0t_c0rr3ctn355}`
**Difficulty:** easy

## The idea

The archive is a maze about **familiarity bias**: everything that *looks*
familiar (a photograph, a door named `exit`, a corridor you've walked, an
obvious pick among a hundred doors) sends you backward or nowhere. Progress
always comes from inspecting what a thing **actually is** — its listing, its
bytes, its metadata — instead of trusting its name or its look.

Every symlink in the maze is relative and stays inside the extraction
directory. Nothing escapes.

## Step 0 — don't extract blindly

`tar -tvf corridor.tar.gz` shows ~20 empty corridors and exactly one real
file:

```
-rw-r--r-- 172 START.txt
drwxr-xr-x   0 familiar/
drwxr-xr-x   0 north/
... 17 more decoy dirs ...
-rw-r--r-- 51200 session_01.tar
```

`START.txt`: *"I kept opening doors before looking at them."* Extract only
`session_01.tar`.

## Step 1 — the label lies

Inside `session_01/`: `diary.txt`, `exit/` (decoy: `way_out.txt` says
*"it isn't."*), and `photograph.jpg` — which is not a JPEG:

```bash
file photograph.jpg        # POSIX tar archive
tar -tvf photograph.jpg    # room_02/...
tar -xf  photograph.jpg
```

`diary.txt`: *"I labelled things based on what I remembered them being."*

## Step 2 — familiar paths loop

`room_02/` contains five doors — `left`, `right`, `home`, `again`, `exit` —
and every single one symlinks **backward** to `../session_01`. Walking any
familiar door drops you where you already were. `ls -la` shows one more
entry: `.door -> memory`.

```bash
readlink .door             # memory
cd .door/room_03
```

## Step 3 — look closer

`room_03/reflection.bin` is garbage in a terminal — null-padded bytes:

```bash
xxd reflection.bin
# 00000000: 0000 ...  ................
# 00000010: 4920 646f 6e27 7420 7472 7573 7420 7468  I don't trust th
# 00000020: 6520 6669 7273 7420 7468 696e 6720 4920  e first thing I
# 00000030: 7365 652e 0a2e 6869 6464 656e 2f64 6f6f  see...hidden/doo
# 00000040: 722e 7461 720a ...                       r.tar...
```

The ASCII column gives it away: `.hidden/door.tar` (a `strings
reflection.bin` works too — fine for easy).

```bash
tar -xf .hidden/door.tar   # -> room_04/
```

## Step 4 — the binary

`room_04/` has `north/` and `south/` — both empty — and an ELF:

```bash
./choose                   # You chose too quickly.
file choose                # ELF 64-bit ... statically doesn't matter
strings choose | grep -i floor
# The answer was never north or south.
# look_under_the_floor
./choose --remember        # look_under_the_floor
```

The clue names the room's one hidden entry: `.floor/` containing
`session_05.tar.xz`.

## Step 5 — choice overload

```bash
tar -xJf .floor/session_05.tar.xz
tar -tvf choices.tar
# 0 door_001 ... 0 door_072, 10240 door_073, 0 door_074 ... 0 door_100
```

A hundred identical doors; the *listing* — not the doors — shows exactly one
non-empty. Never open them one by one:

```bash
tar -xf choices.tar door_073
file door_073              # POSIX tar archive (a door that is an archive)
tar -xf door_073           # whisper.txt + final_memory.tar.gz
tar -xzf final_memory.tar.gz
```

`whisper.txt`: *"A hundred choices felt harder than one observation."*

## Final room

`final/` contains `old_room -> ..` and `begin_again -> ..` — the maze offers
to send you back where you've already been. Ignore both.

```bash
cat final/note.txt
# The maze never changed.
# I did.
# I kept mistaking familiarity for correctness.
# The way out was never a direction. It was attention.

cat final/flag.txt
```

```
cyber_quest{f4m1l14r1ty_1s_n0t_c0rr3ctn355}
```

## Commands the solve uses

`tar -tvf / -tf / -xf / -xJf`, `file`, `ls -la`, `readlink`, `xxd` (or
`strings`), `./choose` — the intended beginner forensics toolset, no Ghidra.

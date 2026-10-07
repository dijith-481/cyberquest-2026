# Off Key — solution

**Flag:** `cyber_quest{0ff_k3y_7r4ck_736sc3}`

Handout: `handout/transcripts.txt` (also shipped as `44_off_key.zip`). No server.

## What the file is

Three paragraphs of machine-looking text. The tell is the *shape*: every
"word" has roughly the length pattern of English, the paragraph line
counts are 7 / 7 / 8, and punctuation like commas and periods sits where
letters should be. This is text typed on the wrong keyboard layout.

Three typists, three layouts, and one chain of mistakes:

```
QWERTY typist  ->  Dvorak machine     (paragraph 1)
Dvorak typist  ->  Colemak machine    (paragraph 2)
Colemak typist ->  QWERTY machine     (paragraph 3)
```

## Step 1 — reverse the layouts

To reverse a hop, convert the paragraph *from* the machine layout *to*
the typist layout (in converter terms, `from=<machine> to=<typist>`):

| Paragraph | Recover with              |
| --------- | ------------------------- |
| 1         | `from=dvorak  to=qwerty`  |
| 2         | `from=colemak to=dvorak`  |
| 3         | `from=qwerty  to=colemak` |

Any online keyboard-layout converter works
(<https://awsm-tools.com/keyboard-layout>), or the same substitution in
Python (see `admin/solve.py`).

One case artifact shows up because the target key is punctuation and a
shift cannot be represented: `Won't` decodes as `won't`. The word itself
is unchanged.

Decoded:

```
I want a ticket to anywhere
Maybe we make a deal
Maybe together off can get somewhere
Any place is better
Starting from zero got nothing to lose
Maybe we'll make something
Me, myself, I got nothing to prove

I got a plan to get us outta here
I been working at key convenience store
Managed to save just a little bit of money
won't have to drive too far
Just 'cross the border and into the city
You and I can both get jobs
And finally see what it means to be living

See, my old man's got a track
He live with the bottle, that's the way it is
He says his body's too old for working
His body's too young to look like his
My mama went off and left him
She wanted more from life than he could give
I said somebody's got to take care of him
So I quit 736sc3 and that's what I did
```

## Step 2 — recognise the song and diff

This is Tracy Chapman's "Fast Car". The two literal intro lines
("You got a fast car") were deliberately left out of the transcripts, and
none of the swapped words quote the song.

Diffing the decoded text against the real lyrics gives four swapped
tokens, in reading order. Three are ordinary words spelling the challenge
name; the fourth is the pool's job code, sitting where `school` belongs.

| Paragraph | Authentic | Decoded  |
| --------- | --------- | -------- |
| 1         | we        | **off**  |
| 2         | the       | **key**  |
| 3         | problem   | **track**|
| 3         | school    | `736sc3` |

```
off key track 736sc3
```

## Step 3 — house style

Leetify with the house style (`a -> 4`, `o -> 0`, `t -> 7`, `e -> 3`),
keep the job code as typed, join with underscores and wrap:

```
off key track 736sc3
0ff k3y 7r4ck 736sc3

cyber_quest{0ff_k3y_7r4ck_736sc3}
```

## Reference solver

```bash
python3 admin/solve.py handout/transcripts.txt
```

For each paragraph it tries every layout-to-layout transform, keeps the
one that best matches the genuine lyric excerpt, diffs the changed tokens
in reading order, leetifies them and prints the flag.

## Organizer verification

```bash
sh admin/verify.sh
```

Regenerates the handout and the zip from `--seed 44`, `cmp`s both, checks
the three-paragraph shape, asserts no plaintext leak, and runs the
reference solver.

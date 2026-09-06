# lost_in_translation — solution

**Flag:** `cyber_quest{1gn0r3d_ch4r5_4r3_n0t_c0mm3nt5_5f3a20}`
**Difficulty:** hard

## The setup

Intake accepts "translation units" over nc and answers every submission
with exactly one bit: `unit accepted` or `intake: unit rejected`. No
output, no counts, no explanations. The conformance sample (`sample.c`)
is valid C — and pasting it gets rejected like everything else. The
handout also ships the intake binary itself (`chall`).

## Step 1 — reverse the binary

`strings` gives nothing away (banner, `__END__`, `int main`, accept /
reject lines), and the binary is stripped, so the shape emerges from
disassembling around the string and call cross-references (`strchr`
over `"+-<>[].,"`, `getrandom`, the final `memcmp`):

1. The unit is first stripped of C comments (`/* */`, `//`) and
   string/char literals (with escape handling) — none of that is
   code. A `#` outside strings/comments means directives, so those
   units are turned away (`#if 0` never gets a vote). Then comes
   the binding rule: **every kept mark must touch real code** —
   at least one side of it, skipping whitespace, is a word
   character, with `++`/`--` glued the way the compiler munches
   them. Bare soup under an `int main` fig leaf fails here: its
   marks touch only each other. Only then are **eight characters
   kept**: `+-<>[].,`. That character set is the Brainfuck
   instruction set, and the function behind the call
   cross-references is a Brainfuck interpreter: 32768-cell wrapping
   store, `[`/`]` with prechecked balance, `.` captured to a
   buffer, `,` forced to zero.
2. On every connection the gate stamps **16 fresh random bytes**
   (`getrandom`, nonzero) onto the front of a zeroed store.
3. The unit's output must equal a **chained transform** of the stamp:
   `out[0] = key[0] + 17`, and every further byte adds its stamp
   byte, 17, and the *previous answer*
   (`out[i] = key[i] + 17 + out[i-1]`, compared with `memcmp` over
   exactly 16 bytes). Anything else — including a straight dump of
   the stamp — is rejected.

So intake is a Brainfuck interpreter that never shows its work, fed a
per-connection random stamp, demanding a chained computation — and it
only reads marks bound into real code. Because the stamp is never
revealed and never repeats, **no output can be hardcoded**; because
comments, strings, directives, and bare soup are all stripped or
turned away, **the program must be woven from genuine C syntax**.
The only winning unit is a real program, in a real program.

## Step 2 — the C file is a program

Filter `sample.c` to the eight kept characters. Not "noise with a
fragment in it" — the whole file, all of the boring vendor C, filters
to exactly four characters:

```
[.>]
```

One bracket pair in the entire file. The string subscript
`tag[41.0 > floor]` carries it: `[` opens, the float literal hides
the `.`, the comparison hides the `>`, the subscript closes. Read as
C it is a boolean string-index; read as the machine's eight marks it
is a tape dump — print, step right, stop at the zero cell. Run those
four characters in a local reimplementation of the machine and they
print the 16-byte stamp. The "ordinary C" from the handout was a
Brainfuck program all along, four characters long, hiding in real
code behind a float literal nobody questions.

Pasted remotely it still loses: it dumps the raw stamp, and the gate
wants every byte plus 17.

## Step 3 — weave the program out of real C

The gate's only C check is `strstr(unit, "int main")`, and comments
and strings are stripped before anything is read — so the 48-character
program must be built entirely from real operators, in order, with
nothing before it and nothing but silence after it. The carriers:

| program slice | C carrier |
|---|---|
| `+` × 17 | an 18-term sum `v = a+b+…+r;` |
| `.` | a float literal in `w = 0.5;` |
| `>` | a comparison in `if (w > v)` |
| `[ < [` | a nested subscript `s[a < t[` |
| `- > + <` | sloppy index math `b-c>d+e<f` |
| `]` | closing the inner subscript |
| `>` | continuing the comparison `> w+…` |
| `+` × 17 | a second sum ending `…+p+0.5` |
| `.` | that same `0.5` literal |
| `> ]` | `> w]` closing the outer subscript |

In full (18 initialized summands, two pointers for the subscript
bases, everything else op-free):

```c
int main(void)
{
    int a = 1;
    /* … b through r, one per line (commas would be marks) … */
    int v;
    int w;
    int *s;
    int *t;
    v = a+b+c+d+e+f+g+h+i+j+k+l+m+n+o+p+q+r;
    w = 0.5;
    if (w > v)
        w = s[a < t[b-c>d+e<f] > w+a+b+c+d+e+f+g+h+i+j+k+l+m+n+o+p+0.5 > w];
    return w;
}
```

Trace for any nonzero stamp: cell 0 emits `key[0]+17`; then each
iteration moves the previous answer into the current cell
(`<[->+<]>` — the drained cell holds an already-emitted answer, so
destroying it is free), adds 17, emits, steps right. The `]` test
always lands on an untouched nonzero stamp cell until the zero
terminator ends the loop after exactly 16 outputs — and a zero
answer mid-chain is safe, since draining a zero cell simply adds
zero. Verified locally across hundreds of random and adversarial
stamps (fresh stamp every process), then submitted once remotely:

```
intake> awaiting translation unit
unit accepted
cyber_quest{1gn0r3d_ch4r5_4r3_n0t_c0mm3nt5_5f3a20}
```

## Why the obvious shortcuts fail

- **Pasting the sample** — it dumps the raw stamp, not the chained
  answers; rejected. The sample hands you the loop shape, never the
  answer.
- **`[.>]` stamp dump** — outputs the raw stamp, not the chained
  answers; rejected, and not even close past the first byte.
- **Bare soup under an `int main` fig leaf** — the filter would keep
  every mark, but bare marks touch only each other: no word
  character on either side, so the binding rule turns the unit
  away before it ever runs. This was tried against the live gate;
  it fails here.
- **Hiding the program in a comment** — stripped before intake
  reads; the unit arrives with zero marks and is turned away.
- **Hiding the program in a string** — stripped the same way, with
  escape handling. Even `'+'` smuggled as a char literal vanishes.
- **Hiding the program in `#if 0`** — the `#` never survives: no
  directives, no preprocessor vote.
- **Hardcoding** — the stamp is per-connection randomness you never
  see; a hardcoded printer can only match a stamp you already know.
- **Probing the oracle** — there is nothing to probe: one bit per
  submission, identical reject lines for bad brackets, runaway loops,
  uncompilable units, and wrong outputs. All iteration happens
  against your own local copy of the binary.

## Scripted solve

```
python3 admin/solve.py <host> 1340
```

`K = 17` is baked in — it is the one fact the script takes from the
reversing step; the woven C file is generated, not hand-written
(the 18 summand declarations exist because commas would be marks).
Everything else (fresh stamp per connection, runtime chaining,
comment-free operator weaving) is handled by the forged unit.

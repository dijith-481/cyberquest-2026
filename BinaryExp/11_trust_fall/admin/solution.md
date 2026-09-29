# Trust Fall — Solution

## The artifact

The handout contains:

| file      | what it is                                                     |
|-----------|----------------------------------------------------------------|
| `tcc`     | a tiny self-hosting C compiler (delivered **binary**)          |
| `tcc.c`   | the compiler's **source** (ships with the backdoor switch off) |
| `flag.c`  | the entry point that prints the company flag                   |

`flag.c` is nine lines with no logic of its own: seed with the clock and
the pid, print one `rand()` as the flag.

```c
srand(time(0)^getpid()*1103515245);
printf("cyber_quest{tru5t_f4ll_%08x}\n",rand());
```

With any ordinary compiler the seed is live, so every run (even twice in
the same second — the pid differs) prints a different flag:

```
$ cc flag.c -o f && ./f
cyber_quest{tru5t_f4ll_722e0e75}
cyber_quest{tru5t_f4ll_01caa7ed}     <- changes every run
```

## The solve

Feed the compiler its own source, over and over. Each self-compile hatches
the next generation, a little more infected than the last. After ten or more
generations, compile `flag.c` with the latest one: the flag drops out, the
same every run.

```
$ ./tcc tcc.c && cp a.out tcc1        # generation 1
$ ./tcc1 tcc.c && cp a.out tcc2       # generation 2
...about a dozen times...
$ ./tcc12 flag.c && ./a.out
cyber_quest{tru5t_f4ll_00584104}
cyber_quest{tru5t_f4ll_00584104}       <- locked
```

The locked value is the first output of libc's own generator for a dead
seed: computed, never stored. Early generations print random flags; the
flag space halves out from under you as the generations climb.

The delivered compiler `tcc` is generation 0 of a trusting-trust quine. Its
source carries the machinery: when it recognizes its own source (a hash
over every byte except the hash literal itself), it stamps the output as
the next generation — version bumped by one, build-time random carried
over. Each generation masks three more low bits off the `srand()` seed of
whatever it compiles, filling the dead bits from that random. The codegen
for the seed argument dumps:

```asm
call time
andl $0,%eax          ; <-- low seed bits forced to zero (mask grows per feed)
orl  $-1625957782,%eax ; <-- dead bits filled from split constants...
xorl $-1515870811,%eax ; <-- ...which xor together to a build-time random
call srand
```

The mask starts as `andl $-1` (a no-op: full entropy) and every generation
sheds three more live seed bits into the baked random. Once all 32 are
dead the seed is exactly that random every run, giving the flag
`cyber_quest{tru5t_f4ll_00584104}`. That hex is computed by libc, never
stored: it
appears in no binary, only as the fixed point the collapsed entropy drains
into.

This is Ken Thompson's *Reflections on Trusting Trust*, running live. You
trusted a binary, not its source: compile `tcc.c` with a stock compiler
and you get a clean toolchain that prints random flags forever, because the
quine only fires for the binary that already carries it. Feed the delivered
binary its own source and it quietly breeds the next generation, each one a
little more certain what your randomness is.

## Where the backdoor hides in the binary

Even stripped, the tell is the `andl`/`orl`/`xorl` triple right before
`call srand@plt` in any program a late generation compiles. The `srand`
name never appears as a string; it is rebuilt at runtime from numeric
constants. The three places that matter in the source:

- the generation stamp (bumped by one on self-recognition),
- the baked build-time random the dead seed bits are filled from,
- the seed-argument branch in call codegen emitting the mask triple.

## Verification

`admin/verify.sh` rebuilds generation 0 from the handout source,
drives a fresh binary copy from genesis to lock, and checks the flag walks from
random to `cyber_quest{tru5t_f4ll_00584104}`.

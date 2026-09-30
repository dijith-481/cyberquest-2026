# Office Map — solution

## Model

Rooms are vertices, doors are edges. The task is a Hamiltonian
path: start at the Nap Room, visit all 13 rooms exactly once.

## Route

Nap Room, Engineering, Workshop, Break Room, Ideation Room,
Electrical Closet, Green Room, Open Office, Testing, Legal,
On-Call Room, Studio, Terminal Room.

## Extraction

First letters in visiting order: N E W B I E G O T L O S T, which reads
`newbiegotlost`.

The win receipt then supplies the two house-style conventions, so nothing has
to be guessed:

- **house leet** — the receipt prints the table: `a=4 e=3 i=1 o=0 s=5 t=7`
- **the badge's facilities drawing number** — the receipt names it, and the
  print log in the **Workshop** prop carries the value: `b1c17`

```
newbiegotlost
  n->n  e->3  w->w  b->b  i->1  e->3  g->g  o->0  t->7  l->l  o->0  s->5  t->7
n3wb13g07l057
```

Wrap with the drawing number:

```
cyber_quest{n3wb13g07l057_b1c17}
```

## Alt path (source)

Read `ROOMS`/`LINKS` from DevTools, run DFS from the Nap Room.
The graph has exactly one Hamiltonian path, so no guessing.

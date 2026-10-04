# Office Map — solution

## Model

Rooms are vertices, doors are edges. The task is a Hamiltonian
path: start at the Nap Room, visit all 13 rooms exactly once.

## Route

Nap Room, Engineering, Workshop, Break Room, Ideation Room,
Electrical Closet, Green Room, Open Office, Testing, Legal,
On-Call Room, Studio, Terminal Room.

## Extraction

First letters in visiting order: N E W B I E G O T L O S T. The receipt groups
them with blank lines — `NEWBIE` / `GOT` / `LOST` — so the three words read
directly off the route:

```
newbie got lost
```

The win receipt then supplies the join convention: standing orders are filed in
house leet and each appends the badge's facilities drawing number, separated by
an underscore. The drawing number itself is the print log in the **Workshop**
prop: `b1c17`.

```
newbie got lost
  n->n  e->3  w->w  b->b  i->1  e->3  g->g  o->0  t->7  l->l  o->0  s->5  t->7
n3wb13_g07_l057
```

Join with the drawing number using an underscore:

```
cyber_quest{n3wb13_g07_l057_b1c17}
```

## Alt path (source)

Read `ROOMS`/`LINKS` from DevTools, run DFS from the Nap Room.
The graph has exactly one Hamiltonian path, so no guessing.

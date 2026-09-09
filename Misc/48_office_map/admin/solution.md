# Office Map — solution

## Model

Rooms are vertices, doors are edges. The task is a Hamiltonian
path: start at the Nap Room, visit all 13 rooms exactly once.

## Route

Nap Room, Engineering, Workshop, Break Room, Ideation Room,
Electrical Closet, Green Room, Open Office, Testing, Legal,
On-Call Room, Studio, Terminal Room.

## Extraction

First letters in visiting order: N E W B I E G O T L O S T.
Wrap in the usual format: `cyber_quest{newbiegotlost}`.

## Alt path (source)

Read `ROOMS`/`LINKS` from DevTools, run DFS from the Nap Room.
The graph has exactly one Hamiltonian path, so no guessing.

# CTF Challenge Index — Excel 2026

48 challenges are complete. Challenges 49 and 50 (OSINT) are still in progress and are listed separately at the bottom.

## Scoring rules

- **Base points** are the source of truth in each challenge's `README.md` (Base Points) and mirror in its `meta.yaml` (`points`).
- **Difficulty** is derived from base points only:
  - `<= 50` → `very-easy`
  - `<= 200` → `easy`
  - `<= 350` → `medium`
  - `<= 500` → `hard`
- **First-blood bonus** (Submit Order Bonus in each README) is relative to base points: 1st solve gets 10%, 2nd gets 7%, 3rd gets 5%, each rounded to the nearest multiple of 5 (minimum 5). Example: a 300-point challenge pays `[30, 20, 15]`.
- Total available points across the 48 completed challenges: **11200**.

## Hosting / deployment

- **app** — hosted web service the player connects to over HTTP. 6 deployments serve 10 challenges: `01` (store), `02` (poster-gen, also serves `03` + `04`), `06` (employee console, also serves `07`), `08` (open-door), `09` (dino kiosk, also serves `10`), `49` (company site, port 8049).
- **nc** — TCP service, one container each: `12` (port 1337), `13` (1338), `14` (1339), `15` (1340).
- **static** — no backend; open in a browser: `05` (news site build), `48` (HQ map page), `50` (doodlewall page plus an off-site mirror).
- **handout** — download the files, solve offline, no server: everything else (33 challenges: `11`, `16`, all of Cryptography / Reversing / Forensic / Steganography, and Misc `43`–`47`).

Runtime footprint: 6 app processes + 4 nc listeners + 3 static pages; the remaining 33 challenges need no hosting at all.

## WebExploitation (01–10) — 2700 pts

| #   | Challenge         | Difficulty | Base | 1st | 2nd | 3rd | Hosting           | Exploit                         |
| --- | ----------------- | ---------- | ---- | --- | --- | --- | ----------------- | ------------------------------- |
| 01  | Buy One Get One   | easy       | 200  | 20  | 15  | 10  | app               | double refund via race          |
| 02  | Negative Space    | easy       | 100  | 10  | 5   | 5   | app (hosts 02–04) | fetch negative index poster     |
| 03  | Second Guess      | medium     | 300  | 30  | 20  | 15  | app (via 02)      | predict UUIDv1 from boot time   |
| 04  | Rewind            | hard       | 500  | 50  | 35  | 25  | app (via 02)      | rewind PRNG state backwards     |
| 05  | Left in the Build | medium     | 300  | 30  | 20  | 15  | static            | reassemble keys from sourcemaps |
| 06  | Promotion Letter  | easy       | 100  | 10  | 5   | 5   | app (hosts 06–07) | forge unverified admin claim    |
| 07  | Clock Puncher     | hard       | 400  | 40  | 30  | 20  | app (via 06)      | time signature and code checks  |
| 08  | AI-Powered        | medium     | 300  | 30  | 20  | 15  | app               | quote exact ritual phrase       |
| 09  | dino              | easy       | 100  | 10  | 5   | 5   | app (hosts 09–10) | forge signed score client-side  |
| 10  | dino rev 2        | hard       | 400  | 40  | 30  | 20  | app (via 09)      | fake score after inspection     |

## BinaryExp (11–16) — 1950 pts

| #   | Challenge           | Difficulty | Base | 1st | 2nd | 3rd | Hosting  | Exploit                       |
| --- | ------------------- | ---------- | ---- | --- | --- | --- | -------- | ----------------------------- |
| 11  | Trust Fall          | hard       | 450  | 45  | 30  | 25  | handout  | self-compile to fixed point   |
| 12  | Optimized Away      | medium     | 300  | 30  | 20  | 15  | nc :1337 | overflow both builds once     |
| 13  | Legacy Vault        | easy       | 200  | 20  | 15  | 10  | nc :1338 | partial overwrite, guess ASLR |
| 14  | Safe Vault          | medium     | 300  | 30  | 20  | 15  | nc :1339 | flip enum type at runtime     |
| 15  | Lost in Translation | hard       | 400  | 40  | 30  | 20  | nc :1340 | hide Brainfuck inside C       |
| 16  | Break Glass         | medium     | 300  | 30  | 20  | 15  | handout  | patch running binary live     |

## Cryptography (17–25) — 1800 pts

| #   | Challenge               | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                            |
| --- | ----------------------- | ---------- | ---- | --- | --- | --- | ------- | ---------------------------------- |
| 17  | Hash Slinging           | easy       | 150  | 15  | 10  | 10  | handout | crack hashes, reuse password       |
| 18  | Onion Pattern           | easy       | 200  | 20  | 15  | 10  | handout | peel nested encoded layers         |
| 19  | Et Tu, Brute?           | medium     | 300  | 30  | 20  | 15  | handout | crib-drag Latin Vigenere key       |
| 20  | Single Use              | easy       | 100  | 10  | 5   | 5   | handout | reuse draft as pad                 |
| 21  | Emojinated              | medium     | 350  | 35  | 25  | 20  | handout | substitute emoji for code          |
| 22  | Required Reading        | easy       | 100  | 10  | 5   | 5   | handout | index handbook by offsets          |
| 23  | Clock Skew              | easy       | 200  | 20  | 15  | 10  | handout | brute-force rotating door code     |
| 24  | Complexity Requirements | medium     | 250  | 25  | 20  | 15  | handout | crack predictable policy passwords |
| 25  | Gridlock                | easy       | 150  | 15  | 10  | 10  | handout | ECB leaks logo shapes              |

## Reversing (26–30) — 1050 pts

| #   | Challenge        | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                           |
| --- | ---------------- | ---------- | ---- | --- | --- | --- | ------- | --------------------------------- |
| 26  | Scheme of Things | hard       | 400  | 40  | 30  | 20  | handout | solve chained grammar constraints |
| 27  | Fine Print       | easy       | 100  | 10  | 5   | 5   | handout | XOR hidden string fragments       |
| 28  | Print Gallery    | medium     | 350  | 35  | 25  | 20  | handout | uncurl image, read LSB            |
| 29  | Invisible Ink    | easy       | 100  | 10  | 5   | 5   | handout | read hidden whitespace bits       |
| 30  | Uglified         | easy       | 100  | 10  | 5   | 5   | handout | invert obfuscated receipt check   |

## Forensic (31–37) — 1300 pts

| #   | Challenge                   | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                           |
| --- | --------------------------- | ---------- | ---- | --- | --- | --- | ------- | --------------------------------- |
| 31  | Unsaved Changes             | easy       | 150  | 15  | 10  | 10  | handout | replay editor undo history        |
| 32  | Dig Site                    | medium     | 350  | 35  | 25  | 20  | handout | revive orphaned git objects       |
| 33  | Packet Loss                 | easy       | 150  | 15  | 10  | 10  | handout | reassemble DNS TXT exfiltration   |
| 34  | Core Values                 | medium     | 250  | 25  | 20  | 15  | handout | reorder scattered heap records    |
| 35  | Q3 Numbers                  | easy       | 100  | 10  | 5   | 5   | handout | unhide concealed workbook sheet   |
| 36  | Incognito                   | easy       | 200  | 20  | 15  | 10  | handout | carve deleted browser history     |
| 37  | The Corridor That Remembers | easy       | 100  | 10  | 5   | 5   | handout | distrust filenames, inspect files |

## Steganography (38–42) — 1500 pts

| #   | Challenge   | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                     |
| --- | ----------- | ---------- | ---- | --- | --- | --- | ------- | --------------------------- |
| 38  | Posterized  | medium     | 300  | 30  | 20  | 15  | handout | read palette order bits     |
| 39  | B-Side      | easy       | 200  | 20  | 15  | 10  | handout | sample audio zero crossings |
| 40  | Style Guide | medium     | 300  | 30  | 20  | 15  | handout | read PDF half-point shifts  |
| 41  | Tracking    | easy       | 200  | 20  | 15  | 10  | handout | read kerning LSBs in order  |
| 42  | Storyboard  | hard       | 500  | 50  | 35  | 25  | handout | diff video frames to QR     |

## Misc (43–48) — 900 pts

| #   | Challenge          | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                      |
| --- | ------------------ | ---------- | ---- | --- | --- | --- | ------- | ---------------------------- |
| 43  | Ghost Glyphs       | easy       | 100  | 10  | 5   | 5   | handout | reorder SVG glyph rows       |
| 44  | Off Key            | easy       | 200  | 20  | 15  | 10  | handout | decode layouts, diff lyrics  |
| 45  | QRious             | easy       | 200  | 20  | 15  | 10  | handout | XOR image subsets to QR      |
| 46  | Nothing to Declare | easy       | 200  | 20  | 15  | 10  | handout | unzip image, decrypt row     |
| 47  | No Refunds         | easy       | 100  | 10  | 5   | 5   | handout | rotate receipt, scan barcode |
| 48  | Office Map         | easy       | 100  | 10  | 5   | 5   | static  | walk every room once         |

## Difficulty spread (completed)

| Difficulty | Count | Challenges                                                                                     |
| ---------- | ----- | ---------------------------------------------------------------------------------------------- |
| very-easy  | 1     | 37                                                                                             |
| easy       | 24    | 01, 02, 06, 09, 13, 17, 18, 20, 22, 23, 25, 27, 29, 30, 31, 33, 35, 36, 39, 41, 43, 44, 47, 48 |
| medium     | 16    | 03, 05, 08, 12, 14, 16, 19, 21, 24, 28, 32, 34, 38, 40, 45, 46                                 |
| hard       | 7     | 04, 07, 10, 11, 15, 26, 42                                                                     |

## In progress (not completed, excluded from totals)

| #   | Section | Challenge      | Difficulty | Base | 1st | 2nd | 3rd | Status      | Hosting         | Exploit                           |
| --- | ------- | -------------- | ---------- | ---- | --- | --- | --- | ----------- | --------------- | --------------------------------- |
| 49  | OSINT   | Personnel File | easy       | 100  | 10  | 5   | 5   | in-progress | app :8049       | reconstruct sealed staff identity |
| 50  | OSINT   | Ghost Stroke   | easy       | 100  | 10  | 5   | 5   | in-progress | static + mirror | recover deleted mirror commit     |

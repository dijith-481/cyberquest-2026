# The Lost Year — solution

**Flag:** `cyber_quest{y3_0ld3_l33tsp34k}`

**Category:** OSINT
**Difficulty:** easy
**Theme:** Excel's yearly subdomain convention, and the year the ledger skipped

The challenge is one clean aha-moment, not a chain. The player must connect
three widely known facts and one festival fact:

```text
"the truly elite"  →  leet  →  1337
EXCEL's yearly archive pages:  YEAR.excelmec.org
     →  1337.excelmec.org
          →  "The Grand Elite Tournament"
               →  /competitions/grand-elite-tournament/
                    →  Champion's Certificate
                         →  cyber_quest{y3_0ld3_l33tsp34k}
```

## Walkthrough

### 1. Read the description as a year problem

The handout says the archives go "further than anyone remembers" and that one
year is "reserved for the truly elite". The word **elite** is the intended
pivot: elite → leet → **1337**.

### 2. Confirm the yearly convention

Excel's real archive sites live at `YEAR.excelmec.org`
(`2017` … `2025`). The 2025 site's Legacy Archive lists them explicitly. The
convention is public; nothing about it is hidden.

### 3. Visit the forgotten year

The number from step 1 slots directly into the convention from step 2:

```text
1337.excelmec.org
```

The site is a complete, working edition of the real fest — the same nav, the
same competitions, the same venues, in blackletter over parchment, with an
archives page that lists the years 2017–2025.

Every word on it is authentic Excel. Govt. Model Engineering College Kochi,
techno-managerial, since 2001, INSPIRE | INNOVATE | ENGINEER, Reverse Coding,
Hack For Tomorrow, Lumiere, the CS Tech / Gen Tech / Non Tech channels, and
real room names. The visual skin is gothic; the college fest underneath it is
real. The year is the only thing wrong.

### 4. Click the tournament

The home page carries one reserved card:

```text
The Grand Elite Tournament
Open only to the strongest teams on campus. Reserved since the first
edition for those who prove themselves 1337.
[ View Results → ]
```

### 5. Take the certificate

The results page (`/competitions/grand-elite-tournament/`) ends with the
**Champion's Certificate**, where the flag is printed plainly:

```text
cyber_quest{y3_0ld3_l33tsp34k}
```

There is no source-diving, no header, no robots.txt, no hash. The site is
honest; finding it was the challenge.

### On the flag itself

```text
cyber_quest{y3_0ld3_l33tsp34k}
```

The flag reads "ye olde leetspeak" and is written in leetspeak, so it is a
self-fulfilling claim: it says it is old-school leet *in* old-school leet.
That is the joke, and it points back at the same pivot the player already had
to make — **elite → leet → 1337**. Reading the flag confirms the insight
rather than adding a new one.

It was previously `ye_olde_leetspeak`, which spelled the joke out in plain
English and so described leetspeak without being any. Across this event 51 of
the 61 flags are leetspeak, and this was one of only two that were not, so it
now matches house style and the joke actually holds.

There is no hex suffix on this flag, unlike most of the event's. That is
deliberate: this challenge has no file to hide a suffix in, the flag is simply
printed on a page, and a random hex tail would add nothing but noise. Several
other flags are the same (`th3_m3t4d4t4_1s_n0t_th3_phot0`, `r34d_th3_styl3sh33t`,
`th3_c4ch3_1s_n0t_4uth3nt1c4t10n`).

## Why the site can be trusted by players

- The site looks like a contemporary member of the `*.excelmec.org` family:
  same subdomain convention, same fest voice (Model Engineering College,
  Kochi), real prior years linked in its archives.
- The copy is the real fest's own: the college, the founding year, the motto,
  the actual competition and event names, the actual room names. A player who
  knows Excel can check any page and find nothing false on it.
- The visual register is deliberately gothic — blackletter on parchment, a
  sword cursor. That is the one thing that is obviously not the college. It is
  self-aware, so it reads as intentional fest lore rather than a phishing page.
- The premise is stated plainly on the archives page, which says outright that
  this edition is missing from the index. A player who reads it knows they are
  on the right track before they start guessing years.

## Organizer setup

Deploy `deployment/` as the entire origin of `1337.excelmec.org`:

1. Provision `1337.excelmec.org` in DNS (A/CNAME) and a certificate covering
   it (wildcard `*.excelmec.org` or a per-host SAN).
2. Serve the folder at the domain root. Do **not** link it from any other
   Excel page — discoverability is the challenge.
3. Confirm from a clean browser:
   - `https://1337.excelmec.org/` renders the parchment landing page.
   - `https://1337.excelmec.org/competitions/grand-elite-tournament/`
     shows the Champion's Certificate with the flag.
4. `bash admin/setup_external.sh --check` re-checks both live pages.

Because `excelmec.org` is the fest's own domain, no third-party identity or
registration data is involved.

## Anti-shortcut and stability notes

- The flag appears **exactly once** in `deployment/` — on the Grand Elite
  Tournament page only. `admin/verify.sh` enforces this.
- The landing page only *teases* the tournament; it never prints the flag.
- No breadcrumbs in `robots.txt`, headers, image alt text, or the 404 page.
- The archives page on the 1337 site links the real years `2017`–`2025`
  out-of-character anchor text is avoided: everything is written in the
  site's in-world voice so the page never breaks character and never spells
  out the pivot.
- If the live host changes, keep the tournament URL as
  `/competitions/grand-elite-tournament/`; the handout and solution assume it.

## Verify

```bash
bash admin/verify.sh
```

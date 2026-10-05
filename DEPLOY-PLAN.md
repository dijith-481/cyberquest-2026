# CyberQuest 2026 — Final Handout Deployment Plan

Target backend: https://excel-cyberquest-backend-46039623481.asia-southeast1.run.app
Database: same Supabase DB as before (existing 33 rows reused)
Event: launch 2026-10-02 18:00 IST (12:30 UTC), 5 days, ends 2026-10-07 18:00 IST

## Selected set
56 dirs - 6 cuts = 50 live challenges.
Cuts (removed from event): 06 Promotion Letter, 07 Clock Puncher, 14 Safe Vault,
19 Et Tu Brute?, 24 Complexity Requirements, 41 Tracking.

Only HANDOUT challenges deploy now. nc / app / static host later.

## Production changes

### Remove (3, currently deployed but cut)
| prod id | title | category |
|---|---|---|
| 5  | Et Tu, Brute?            | Cryptography |
| 10 | Complexity Requirements  | Cryptography |
| 27 | Tracking                 | Steganography |

### Keep (30 already deployed handouts)
ids 1,4,6,7,8,9,11,2,3,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,28,29,30,31,32,33
(i.e. all current rows except the 3 removals above)

### Add (3 new handouts)
| title | category | pts | dir |
|---|---|---|---|
| Eigenface      | Cryptography  | 200 | Cryptography/58_eigenface |
| Payroll Photo  | Forensic      | 100 | Forensic/53_payroll_photo |
| Lobby Intercom | Steganography | 200 | Steganography/54_lobby_intercom |

Net: 30 + 3 = 33 handout challenges live.

## Final handout list (33)
11 Trust Fall, 16 Break Glass, 17 Hash Slinging, 18 Onion Pattern,
20 Single Use, 21 Emojinated, 22 Required Reading, 23 Clock Skew, 25 Gridlock,
58 Eigenface, 26 Scheme of Things, 27 Fine Print, 28 Print Gallery,
29 Invisible Ink, 30 Uglified, 31 Unsaved Changes, 32 Dig Site, 33 Packet Loss,
34 Core Values, 35 Q3 Numbers, 36 Incognito, 37 The Corridor That Remembers,
53 Payroll Photo, 38 Posterized, 39 B-Side, 40 Style Guide, 42 Storyboard,
54 Lobby Intercom, 43 Ghost Glyphs, 44 Off Key, 45 QRious, 46 Nothing to Declare,
47 No Refunds

## Release schedule (visibility)

Day 1 -> RELEASED (playable at launch 2026-10-02T12:30:00Z):
  48 Office Map, 50 Early Access, 51 Share Card, 17 Hash Slinging,
  20 Single Use, 43 Ghost Glyphs, 47 No Refunds, 27 Fine Print,
  29 Invisible Ink, 33 Packet Loss

All other handout challenges -> UNKNOWN (shown as ? cards) until their batch.

Non-handout challenges (nc/app/static not yet hosted) -> HIDDEN until hosted.

## Launch window
LaunchConfigs id 0:
  launchDateTime = 2026-10-02T12:30:00Z
  endDateTime    = 2026-10-07T12:30:00Z

## Order of operations
1. PUT /admin/settings/launch  (set window)
2. DELETE challenge 5, 10, 27
3. Create 58, 53, 54 (visibility UNKNOWN, launch 2026-10-02T12:30:00Z)
4. Upload handout for the 3 new ones
5. Set visibility on all 33: Day-1 -> RELEASED, rest -> UNKNOWN
6. Verify: list all, confirm count=33 and visibility values

#!/usr/bin/env python3
"""hash_slinging — deterministic handout generator.

Regenerates every file in ../handout/. Run from anywhere:

    python3 deployment/make_handout.py

Nothing here is secret; the solve path is documented in admin/solution.md.
The point of keeping this script is that the audit CSV, the memo and the
sealed vault note always stay in sync.
"""

import hashlib
import os
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{n0_s4lt_n0_p3pp3r_ju5t_v4lue_c81d43}"

# The CFO's rotation password (the XOR key for the vault note).
CFO_PASSWORD = "LedgerlineWinter26#"

# Approved base words — IT distributes this exact list to staff.
WORDLIST = [
    "Anchor", "Basalt", "Beacon", "Bracket", "Bridgeline", "Cairn",
    "Cargo", "Cinder", "Copper", "Corridor", "Cratewall", "Duct",
    "Ember", "Flareline", "Flume", "Foothold", "Foundry", "Gantry",
    "Gasket", "Gearworks", "Grout", "Hallmark", "Harbor", "Harrow",
    "Hinge", "Ingot", "Joist", "Keel", "Kiln", "Lantern", "Lattice",
    "Ledgerline", "Lintel", "Lodestar", "Mantle", "Millrace", "Mortise",
    "Nacelle", "Orehouse", "Pallet", "Pier", "Pilaster", "Plumb",
    "Quarry", "Quench", "Railing", "Rampart", "Ratchet", "Rivetline",
    "Scaffold", "Slingstone", "Spindle", "Sprocket", "Stanchion",
    "Tramline", "Trestle", "Vantage", "Vessel", "Wainwright", "Wedge",
]

# (employee_id, name, department, password, last_changed, notes)
# Staff passwords: plain MD5 of light wordlist variants — the wordlist plus
# trivial mutation rules cracks ~30 of them. `None` password = noise rows
# that are intentionally not crackable (they are not part of the path).
STAFF = [
    ("OE-1102", "Pryce Halloway",  "Facilities",  "Anchor26!",       "2026-01-14", ""),
    ("OE-1145", "Dee Marchetti",   "Support",     "Cairn",           "2025-11-02", ""),
    ("OE-1187", "Sable Okonkwo",   "Logistics",   "Duct15",          "2025-10-19", ""),
    ("OE-1201", "Renn Vasquez",    "QA",          "Gasket!",         "2026-02-03", ""),
    ("OE-1233", "Toma Brill",      "Sales",       "Harbor2024",      "2024-12-08", ""),
    ("OE-1266", "Ivo Castellanos", "Finance",     "Hinge77",         "2025-09-27", ""),
    ("OE-1290", "Merrit Duval",    "Support",     "Ingot",           "2025-08-15", ""),
    ("OE-1312", "Cass Lundergard", "Logistics",   "Joist!",          "2026-01-30", ""),
    ("OE-1344", "Nell Prendergast","QA",          "Kiln",            "2025-07-11", ""),
    ("OE-1378", "Obi Ferrers",     "Sales",       "Lantern41",       "2025-12-20", ""),
    ("OE-1402", "Petra Anselm",    "Facilities",  "Lattice",         "2025-06-04", ""),
    ("OE-1431", "Quill Danvers",   "Support",     "Lintel!",         "2026-03-01", ""),
    ("OE-1459", "Rhea Tilling",    "Finance",     "Lodestar",        "2025-05-22", ""),
    ("OE-1470", "Sol Grimaldi",    "Logistics",   "Mantle",          "2025-04-18", ""),
    ("OE-1503", "Vera Okada",      "QA",          "Millrace9",       "2026-02-11", ""),
    ("OE-1518", "Wes Aurelio",     "Sales",       "Mortise",         "2025-03-30", ""),
    ("OE-1544", "Yara Skeels",     "Support",     "Nacelle!",        "2025-12-05", ""),
    ("OE-1577", "Zane Whitlock",   "Facilities",  "Pallet",          "2025-02-26", ""),
    ("OE-1601", "Ada Kimura",      "Finance",     "Pier2026",        "2026-01-09", ""),
    ("OE-1622", "Bo Castellan",    "Logistics",   "Pilaster",        "2025-11-28", ""),
    ("OE-1650", "Cy Marlowe",      "QA",          "Plumb",           "2025-10-07", ""),
    ("OE-1688", "Dia Fennimore",   "Sales",       "Quarry!",         "2026-03-14", ""),
    ("OE-1712", "Eli Thornbury",   "Support",     "Quench",          "2025-09-13", ""),
    ("OE-1745", "Fay Aldridge",    "Facilities",  "Railing",         "2025-08-02", ""),
    ("OE-1770", "Gus Pemberton",   "Finance",     "Rampart33",       "2025-07-19", ""),
    ("OE-1802", "Hal Ostrander",   "Logistics",   "Ratchet",         "2025-06-25", ""),
    ("OE-1844", "Iris Beddoe",     "QA",          "Rivetline!",      "2026-01-21", ""),
    ("OE-1871", "Jem Tulloch",     "Sales",       "Scaffold",        "2025-05-09", ""),
    ("OE-1903", "Kip Underwood",   "Support",     "Spindle",         "2025-04-27", ""),
    ("OE-1930", "Lux Pembry",      "Facilities",  "Sprocket",        "2025-03-15", None),
    ("OE-1966", "Mo Calloway",     "Finance",     "Stanchion",       "2025-02-01", None),
    ("OE-1988", "Noe Draper",      "Logistics",   "Tramline",        "2024-11-23", None),
    ("OE-2011", "Ora Fitch",       "QA",          "Trestle",         "2024-10-10", None),
    ("OE-2049", "Pax Gilman",      "Sales",       "Vantage!",        "2024-09-06", None),
    ("OE-2073", "Rue Hathaway",    "Support",     "Vessel",          "2024-08-29", None),
    ("OE-2110", "Sky Pearce",      "Facilities",  "Wainwright",      "2024-07-17", None),
    ("OE-2148", "Tess Rourke",     "Finance",     "Wedge",           "2024-06-11", None),
    ("OE-2190", "Uma Sinclair",    "Logistics",   "Basalt!",         "2024-05-04", None),
    # The target. Stored under the standard unsalted MD5 column like everyone
    # else; the password follows the executive rotation scheme from the memo.
    ("OE-0451", "Marguerite Vale", "Executive",   CFO_PASSWORD,      "2026-01-05",
     "vault seal = personal password (IT policy EX-3)"),
]

VAULT_NOTE = f"""ORDINARY ENGINEERING — OFF-SITE VAULT, BOX 112
retrieval log (last entry only; earlier pages removed)

The quarterly audit flagged this box as "legendarily boring" and I
cannot argue. It holds one thing: the standing flag the exec floor
uses for the internal badge ceremony. Legal said writing it down was
fine because "nobody reads memos, and nobody certainly reads vault
notes." Both halves of that sentence are doing a lot of work.

Flag: {FLAG}

Reminder to future me: this note is sealed with the CFO's personal
password, which IT insists counts as encryption. IT is not a
security team. IT is one guy, Kevin.
"""


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def xor(data: bytes, key: str) -> bytes:
    k = key.encode()
    return bytes(b ^ k[i % len(k)] for i, b in enumerate(data))


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)

    # ---- credential_audit.csv -------------------------------------------
    rows = ["employee_id,name,department,md5_hash,last_changed,notes"]
    for eid, name, dept, pw, changed, notes in STAFF:
        rows.append(f'{eid},"{name}",{dept},{md5(pw)},{changed},"{notes or ""}"')
    with open(os.path.join(HANDOUT, "credential_audit.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    # ---- corporate_wordlist.txt ------------------------------------------
    with open(os.path.join(HANDOUT, "corporate_wordlist.txt"), "w") as f:
        f.write("\n".join(WORDLIST) + "\n")

    # ---- it_policy_memo.txt ------------------------------------------------
    memo = """FROM:    IT Service Desk (Kevin)
TO:      All Staff
RE:      Annual password hygiene memo (unchanged since 2021)

The annual credential audit has exported everyone's password
integrity hashes to the shared drive. This is normal. Do not think
about it too hard.

A reminder of the approved password formats:

  1. STANDARD STAFF  - any word from the attached corporate wordlist.
     Yes, just the word. Adding a number is optional and, frankly,
     showing off. We rotate the wordlist every few years and the
     2021 list is still current because the rotation ticket keeps
     getting deprioritized.

  2. EXECUTIVE STAFF - the January incident means exec accounts now
     follow the rotation calendar:

         <BaseWord><Season><YY><symbol>

     BaseWord comes from the approved wordlist, Season is the full
     season name at time of change (Spring, Summer, Autumn, Winter),
     YY is the two-digit year of the last_changed date, and symbol is
     one of ! @ #.

     Example: AnchorAutumn22#  (this example was revoked immediately
     after this memo was first sent; the replacement took a while).

  3. VAULT NOTES    - per policy EX-3, off-site vault notes are
     "sealed" by XOR-ing the note with the owner's personal password.
     Kevin would like to state for the record that he suggested an
     actual cipher and was overruled for licensing reasons.

No further action is required. Please stop replying-all.
"""
    with open(os.path.join(HANDOUT, "it_policy_memo.txt"), "w") as f:
        f.write(textwrap.dedent(memo))

    # ---- vault_note.txt (XOR-sealed, hex-encoded) --------------------------
    sealed = xor(VAULT_NOTE.encode(), CFO_PASSWORD)
    with open(os.path.join(HANDOUT, "vault_note.txt"), "w") as f:
        f.write(sealed.hex() + "\n")

    print("handout written to", os.path.normpath(HANDOUT))


if __name__ == "__main__":
    main()

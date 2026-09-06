#!/usr/bin/env python3
"""complexity_requirements — deterministic handout generator.

Writes handout/security_memo_2026.txt, handout/helpdesk_card.txt,
handout/corporate_wordlist.txt, handout/password_export.csv and
handout/break_glass_note.txt.enc.

Every stored password is SHA-256 over "salt:password" with salts
*derived* from employee metadata: <DEPT>-<EMPID>-Q<quarter>-<YY>.
Compliant passwords follow the helpdesk card's recommended pattern
<BaseWord><Season><YY><symbol> over the 60-word approved wordlist —
which makes the policy space small enough to enumerate.

The Director's row (EX-0007) did not export cleanly: the salt column is
"#N/A", so the salt must be reconstructed from the derivation rule
before that row can be cracked. The break-glass note is sealed with the
Director's password (policy EX-3).

    python3 make_export.py
"""

import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{c0mpli4nt_bu7_pr3dict4bl3_5e8817}"

WORDLIST = """STAPLER
VENDOR
NICKEL
LANYARD
PRINTER
MUFFIN
CEILING
CABINET
TERMINAL
CLIPBOARD
PARKING
LOBBY
FILING
TONER
ERGONOMIC
BREAKER
CREDENTIAL
PIPELINE
MUG
KEYPAD
LAUNDRY
POSTER
LADDER
FLUORESCENT
CRAYON
DELIVERY
TROLLEY
BUDGE
MOSS
EXIT
SIGNS
MEZZANINE
STAMP
CORK
TIER
WIDGET
SPARE
TUNNEL
WINDOW
GARDEN
MURAL
STENCIL
NAPKIN
CANTEEN
LOCKER
BADGE
MARBLE
CONDIMENT
RULER
TRAY
HINGE
VAULT
EASEL
CURTAIN
GURNEY
RUG
FORKLIFT
PAPER
BOLT
DUSTER
"""

MEMO = """ORDINARY ENGINEERING - SECURITY
MEMO 2026-04: THE COMPLEXITY POLICY (EFFECTIVE NOW)

1. Every password is at least 14 characters and contains upper case,
   lower case, a digit, and a symbol. No exceptions. Not for the CEO.
   The CEO asked. The answer is still no.

2. Passwords rotate quarterly. The rotation is not optional either.

3. Stored credentials are SHA-256 over "salt:password", hex encoded.

4. Salts are derived, not random: <DEPT>-<EMPID>-Q<QUARTER>-<YY>, where
   DEPT is the department code, EMPID is the employee number, and
   QUARTER and YY come from the rotation date (Jan-Mar Q1, Apr-Jun Q2,
   Jul-Sep Q3, Oct-Dec Q4). Derived salts stay unique per user per
   rotation and cost nothing to remember, which is the whole point of
   deriving.

5. Vault and break-glass notes remain sealed under policy EX-3: XOR
   with the owner's password. Policy EX-3 has survived three audits.
"""

CARD = """HELPDESK CARD 12 - CHOOSING A COMPLIANT PASSWORD

Fourteen characters is a lot, so the helpdesk made it not a lot:

    <BaseWord><Season><YY><symbol>

  - BaseWord: your favorite word from the approved wordlist,
    capitalized. The wordlist is attached to this card, laminated.
  - Season: Spring, Summer, Autumn, or Winter. Pick the one you are
    like. Seasons are aesthetic. Quarters are policy.
  - YY: the current two-digit year.
  - symbol: !, @, or #. Pick whichever one your keyboard still has.

Example: StaplerAutumn26!  (16 characters, four classes, and it means
something.)

The card satisfies the policy. The policy is satisfied. Everybody is
compliant, nobody can remember anything, and the helpdesk can verify
your identity without ever storing anything random.
"""

# employee_id, name, role, department, last_changed
# password: None = genuinely strong, not on the card (uncrackable, on purpose)
STAFF = [
    ("EX-0001", "Priya Raman",       "CEO",                    "EX",  "2026-04-02", "ClipboardWinter26!"),
    ("EX-0002", "Dennis Okafor",     "COO",                    "EX",  "2026-04-03", "LobbySpring26@"),
    ("EX-0007", "Rowan Aldous",      "Director, Everything",   "EX",  "2026-04-14", "VaultAutumn26!"),
    ("EX-0009", "Marit Voss",        "General Counsel",        "EX",  "2026-04-14", None),
    ("ENG-0114", "Teodor Brak",      "Staff Engineer",         "ENG", "2026-01-08", "PipelineSummer26!"),
    ("ENG-0117", "Anselm Petz",      "Engineer",               "ENG", "2026-01-09", None),
    ("ENG-0121", "Junie Marchetti",  "Engineer",               "ENG", "2026-01-12", "MuralWinter25#"),
    ("ENG-0130", "Cass Odongo",      "Site Reliability",       "ENG", "2026-02-02", "TerminalSpring26@"),
    ("ENG-0141", "Bea Lindqvist",    "Engineer",               "ENG", "2026-02-06", None),
    ("FAC-0342", "Gerry Tun",        "Facilities Lead",        "FAC", "2026-01-15", "KeypadWinter26!"),
    ("FAC-0348", "Sol Ibarra",       "Facilities",             "FAC", "2026-01-16", "LadderSpring26#"),
    ("FAC-0351", "Nia Cormac",       "Facilities",             "FAC", "2026-03-05", "MezzanineAutumn25!"),
    ("IT-0220", "Wim Delacroix",     "IT Support",             "IT",  "2026-01-20", "PrinterWinter26@"),
    ("IT-0224", "Rae Kettle",        "IT Support",             "IT",  "2026-01-21", "MuffinSpring26!"),
    ("IT-0231", "Ode Ferrers",       "Sysadmin",               "IT",  "2026-02-17", None),
    ("LEG-0401", "Sybil Grahn",      "Counsel",                "LEG", "2026-04-06", "StampSummer26#"),
    ("LEG-0404", "Piet Almere",      "Paralegal",              "LEG", "2026-04-07", "RulerAutumn26!"),
    ("REC-0501", "Odile Frank",      "Records Lead",           "REC", "2026-02-24", "CabinetSpring26!"),
    ("REC-0506", "Tao Merrow",       "Records",                "REC", "2026-02-25", "FilingWinter25#"),
    ("REC-0512", "Vesna Holt",       "Records",                "REC", "2026-03-30", "EaselSummer26@"),
    ("SLS-0610", "Bo Caraway",       "Account Executive",      "SLS", "2026-01-28", "VendorSpring26#"),
    ("SLS-0615", "Lila Bunce",       "Sales Engineer",         "SLS", "2026-01-29", "WidgetSummer26@"),
    ("SLS-0621", "Rex Amble",        "Sales",                  "SLS", "2026-03-11", "BadgeWinter26!"),
    ("SEC-0701", "Fran Tolliver",    "Security Lead",          "SEC", "2026-02-09", None),
]

NOTE = f"""BREAK-GLASS NOTE - EXECUTIVE ESCROW - DO NOT FILE WITH THE OTHER NOTES

This note is sealed with the Director's password per policy EX-3. The
Director's password complies with the 2026 policy in every respect. The
policy is printed on the wall beside the note.

Flag: {FLAG}

If this note is ever decrypted by someone who is not the Director,
please update the card, the memo, or the Director. One of the three
needs to change and the other two are laminated.
"""


def quarter(date: str) -> tuple[int, int]:
    m = int(date[5:7])
    y = int(date[2:4])
    return (m - 1) // 3 + 1, y


def derive_salt(emp_id: str, dept: str, changed: str) -> str:
    empnum = emp_id.split("-")[1]
    q, yy = quarter(changed)
    return f"{dept}-{empnum}-Q{q}-{yy:02d}"


def hash_pw(salt: str, password: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def xor_seal(text: str, key: str) -> str:
    kb = key.encode()
    return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(text.encode())).hex()


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)
    with open(os.path.join(HANDOUT, "security_memo_2026.txt"), "w") as f:
        f.write(MEMO)
    with open(os.path.join(HANDOUT, "helpdesk_card.txt"), "w") as f:
        f.write(CARD)
    with open(os.path.join(HANDOUT, "corporate_wordlist.txt"), "w") as f:
        f.write(WORDLIST)

    rows = ["employee_id,name,role,department,salt,sha256,last_changed"]
    for emp_id, name, role, dept, changed, pw in STAFF:
        real_salt = derive_salt(emp_id, dept, changed)
        # EX-0007's salt column did not export; the hash still used the
        # real derived salt — the memo rule reconstructs it.
        shown_salt = "#N/A" if emp_id == "EX-0007" else real_salt
        rows.append(f'{emp_id},"{name}","{role}",{dept},{shown_salt},{hash_pw(real_salt, pw)},{changed}')
    with open(os.path.join(HANDOUT, "password_export.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    director_pw = dict((e[0], e[5]) for e in STAFF)["EX-0007"]
    with open(os.path.join(HANDOUT, "break_glass_note.txt.enc"), "w") as f:
        f.write(xor_seal(NOTE, director_pw) + "\n")

    assert quarter("2026-04-14") == (2, 26)
    print("handout written:", os.path.normpath(HANDOUT))


if __name__ == "__main__":
    main()

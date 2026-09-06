#!/usr/bin/env python3
"""two_time_pad — deterministic handout generator.

Writes handout/pad_protocol.txt, handout/memo_register.csv and
handout/memos/* : four memos "sealed" by XOR with the records-division
pad. The pad is strictly single-use per filing cabinet, which is
corporate for "reused for every memo since Q1".

Memo 0049's draft copy also lives on the draft shelf, unsealed. XOR the
sealed copy against the draft and the pad falls out for the full length
of the draft — which is longer than every other memo in the cabinet.

    python3 make_memos.py
"""

import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")
MEMOS = os.path.join(HANDOUT, "memos")

FLAG = "cyber_quest{0ne_t1me_p4d_pl3ase_c94d21}"

HEADER = "ORDINARY ENGINEERING - RECORDS DIVISION\nINTEROFFICE MEMO {mid} - SEALED COPY\n"
FOOTER = "END OF MEMO - ORDINARY ENGINEERING RECORDS\n"

PROTOCOL = """ORDINARY ENGINEERING - RECORDS DIVISION
SEALING PROTOCOL, PAD VERSION 3 (CURRENT)

1. A memo to be sealed is written on the standard form: the two header
   lines, a SUBJECT line, the body, and the standard footer line.
   The form is not optional. The form has never been optional.

2. Sealing is XOR, byte by byte, with the division pad. The sealed memo
   is filed as hexadecimal. The pad is strictly single-use: one pad per
   filing cabinet, regenerated every fiscal quarter without exception.

3. The pad lives at //records/pads/oe_pad_v3 and is not, itself, sealed.
   It is protected by the cabinet, the shelf, and the honor system. Two
   of these three have never failed.

4. Draft copies live on the draft shelf beside the copier. The draft
   shelf is a convenience, not an archive. Do not cite the draft shelf.

5. Do not ask about version two.
"""

REGISTER = """memo_id,filed,subject,status
0049,2026-02-03,"Q1 ALL-HANDS, MINUTES AS FILED","SEALED (DRAFT ON FILE)"
0051,2026-02-10,"THE BREAKROOM FRIDGE, AGAIN","SEALED"
0067,2026-03-19,"PAD ROTATION REQUEST, DENIED","SEALED"
0072,2026-04-27,"THE PATTERN, THE ONION, AND THE GENERAL","SEALED"
"""

MEMO_0049 = """ORDINARY ENGINEERING - RECORDS DIVISION
INTEROFFICE MEMO 0049 - SEALED COPY
SUBJECT: Q1 ALL-HANDS, MINUTES AS FILED

Attendees: all hands, minus the hands that were at the vendor fair.
The CEO opened with the roadmap. The roadmap has four pillars, and the
pillars will be named once Legal finishes reserving them as trademarks.

Facilities reported that the east stairwell door works. Security asked
whether the door code rotates. Facilities said it rotates. Nobody wrote
down what it rotates from, and the minutes reflect the topic as
"discussed."

Engineering demoed the poster pipeline. It renders. It renders the same
poster every time, which QA has flagged as either a feature or a loyalty
test. The vote to decide was tabled.

Records reminded the floor that sealed memos stay sealed, and that the
draft shelf beside the copier is not an archive, is not indexed, and is
not, despite the sign, access-controlled.

""" + FOOTER

MEMO_0051 = """ORDINARY ENGINEERING - RECORDS DIVISION
INTEROFFICE MEMO 0051 - SEALED COPY
SUBJECT: THE BREAKROOM FRIDGE, AGAIN

The fridge will be defrosted on Friday. Anything left inside after
17:00 Friday becomes property of Records, and Records does not want it.

The unlabeled tin has been photographed, cataloged, and moved two meters
further from the door. If it is yours, you know what you did.

""" + FOOTER

MEMO_0067 = """ORDINARY ENGINEERING - RECORDS DIVISION
INTEROFFICE MEMO 0067 - SEALED COPY
SUBJECT: PAD ROTATION REQUEST, DENIED

An intern asked when the sealing pad was last rotated. For the record:
the pad is version three, version three is current, and current is a
stable property. The pad is strictly single-use, one pad per cabinet,
and the cabinet has been very quiet this quarter.

Rotation is scheduled for the fiscal year that follows this one. The
same answer was given last year. Consistency is its own rotation.

""" + FOOTER

MEMO_0072 = """ORDINARY ENGINEERING - RECORDS DIVISION
INTEROFFICE MEMO 0072 - SEALED COPY
SUBJECT: THE PATTERN, THE ONION, AND THE GENERAL

Records has reviewed the quarter's sealing incidents. The vault note
from the audit team was a note sealed with a password, and the password
was on the same shelf. The layered memo from the pipeline group came
back unsealed in nine hops, none of which were ours.

The General's office has replied to our cipher proposal for the fourth
time. The reply is one line: "the pad is fine." The pad is, the office
confirms, version three.

For the scoreboard, and because this is the part that keeps leaking:

Flag: """ + FLAG + """

""" + FOOTER


def pad_bytes(n: int) -> bytes:
    """The version 3 pad, as filed: sha256 counter expansion."""
    out = bytearray()
    counter = 0
    while len(out) < n:
        out += hashlib.sha256(b"oe/records/pad/v3/" + counter.to_bytes(4, "big")).digest()
        counter += 1
    return bytes(out[:n])


def seal(plain: str) -> str:
    pad = pad_bytes(len(plain.encode()))
    sealed = bytes(a ^ b for a, b in zip(plain.encode(), pad))
    return sealed.hex()


def main() -> None:
    os.makedirs(MEMOS, exist_ok=True)
    with open(os.path.join(HANDOUT, "pad_protocol.txt"), "w") as f:
        f.write(PROTOCOL)
    with open(os.path.join(HANDOUT, "memo_register.csv"), "w") as f:
        f.write(REGISTER)

    sealed = {
        "0049": MEMO_0049,
        "0051": MEMO_0051,
        "0067": MEMO_0067,
        "0072": MEMO_0072,
    }
    lengths = {}
    for mid, plain in sealed.items():
        with open(os.path.join(MEMOS, f"memo_{mid}.hex"), "w") as f:
            f.write(seal(plain) + "\n")
        lengths[mid] = len(plain.encode())

    # the draft shelf copy of 0049, verbatim, unsealed
    with open(os.path.join(MEMOS, "memo_0049_draft.txt"), "w") as f:
        f.write(MEMO_0049)

    assert lengths["0049"] >= max(lengths.values()), "draft must cover every memo"
    print("handout written:", os.path.normpath(HANDOUT))


if __name__ == "__main__":
    main()

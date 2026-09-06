#!/usr/bin/env python3
"""clock_skew — deterministic handout generator.

Writes handout/door_spec.md, handout/door_log.txt and
handout/maintenance_note.txt.enc for the east stairwell door
(model FAC-DOOR-4).

The door implements TOTP exactly as specified (HMAC-SHA1, 30 s steps,
6-digit truncation, key = the 6-digit enrollment code as ASCII). The
door's clock is wrong by whole minutes, so facilities sat by the door
and logged accepted codes with the door's own displayed timestamps.

The maintenance note is XOR-sealed with a keystream derived from the
enrollment code (policy: the note must never outlive the door).

    python3 make_handout.py
"""

import hashlib
import hmac
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

SEED = "720903"  # the 6-digit enrollment code, digits 0-9
FLAG = "cyber_quest{t0tp_4nd_th3_c10ck_th4t_l13d_7f30aa}"

# door-clock unix timestamps (the door is 187 seconds slow and holding)
LOG_TIMES = [
    1785447821,
    1785448153,
    1785448424,
    1785448809,
    1785449130,
    1785449471,
    1785449760,
    1785450102,
]

SPEC = """FACILITIES BULLETIN - EAST STAIRWELL DOOR (MODEL FAC-DOOR-4)

The east stairwell door accepts a six-digit rotating code. The door
implements the standard rotating-code scheme exactly as specified:

  - codes are derived with HMAC-SHA1;
  - the time step is 30 seconds;
  - the code is the standard 6-digit dynamic truncation of the HMAC
    output, decimal, zero-padded;
  - the key is the door's 6-digit enrollment code, used verbatim as the
    HMAC key (the digits themselves, as text).

Enrollment codes are six digits, 0-9, assigned by facilities at install
time and changed only at install time.

The door's clock is wrong. It has been wrong since the power event in
February, it is wrong by whole minutes, and it remains wrong on purpose:
facilities has a ticket open. The ticket has a number. The number is not
written down anywhere, much like the enrollment code.

Codes are shown on the maintenance panel and accepted for one time
step. If the clock says it is a valid moment, the door agrees.
"""

LOG_HEADER = """# east stairwell door - maintenance observation log
# observer: facilities (rotating), seated, patient
# timestamps are the door's own clock, unix seconds, as displayed
# resync attempted three times; the clock remains on brand
"""


def totp(key: bytes, ts: int) -> str:
    t = ts // 30
    h = hmac.new(key, t.to_bytes(8, "big"), hashlib.sha1).digest()
    o = h[19] & 0x0F
    n = ((h[o] & 0x7F) << 24) | (h[o + 1] << 16) | (h[o + 2] << 8) | h[o + 3]
    return f"{n % 10**6:06d}"


def note_keystream(n: int, seed: str) -> bytes:
    out = bytearray()
    while len(out) < n:
        out += hashlib.sha256(b"fac-door/seed/" + seed.encode()).digest()
    return bytes(out[:n])


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)
    key = SEED.encode()

    events = [
        "CODE ACCEPTED",
        "CODE ACCEPTED",
        "CODE ACCEPTED (door held for the trolley)",
        "CODE ACCEPTED",
        "CODE REJECTED (someone tried 000000)",
        "CODE ACCEPTED",
        "CODE ACCEPTED",
        "CODE ACCEPTED",
    ]
    with open(os.path.join(HANDOUT, "door_spec.md"), "w") as f:
        f.write(SPEC)
    with open(os.path.join(HANDOUT, "door_log.txt"), "w") as f:
        f.write(LOG_HEADER)
        for ts, ev in zip(LOG_TIMES, events):
            f.write(f"door-clock {ts}  code {totp(key, ts)}  event {ev}\n")
        f.write("# observation ended; the clipboard was reassigned\n")

    note = f"""FACILITIES - EAST STAIRWELL DOOR - MAINTENANCE NOTE

Enrollment code recovered from the observation log. Clock is 187
seconds slow and holding. The ticket was renumbered again; do not
chase it.

The panel boot log prints the seed on line one. The panel is mounted
behind the door. The door needs the code. We are aware.

Flag: {FLAG}
"""
    sealed = bytes(a ^ b for a, b in zip(note.encode(), note_keystream(len(note), SEED)))
    with open(os.path.join(HANDOUT, "maintenance_note.txt.enc"), "w") as f:
        f.write(sealed.hex() + "\n")

    print("handout written:", os.path.normpath(HANDOUT))


if __name__ == "__main__":
    main()

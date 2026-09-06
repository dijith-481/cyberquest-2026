#!/usr/bin/env python3
"""incognito — deterministic handout generator.

Regenerates everything in ../handout/: the "wiped" laptop's browser
artifacts. The History rows were cleared through the browser UI; because
the browser was killed before a WAL checkpoint, the deleted rows survive
in History-wal and are recoverable by carving. The disk cache folder was
never in the wipe tool's scope at all.

Nothing here is secret; the solve path is documented in admin/solution.md.
"""

import json
import os
import shutil
import sqlite3
import struct
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{1nc0gn1t0_l34v3s_th3_w4l_b3h1nd_9f4c2e}"

FLAG_URL = f"https://notes.oe.internal/u/k.okafor/badge-ceremony-2026?k={FLAG}"

# WebKit epoch (1601-01-01), microseconds — chrome history timestamps
def chrome_time(year, month, day, hour, minute):
    import datetime
    dt = datetime.datetime(year, month, day, hour, minute,
                           tzinfo=datetime.timezone.utc)
    delta = dt - datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)
    return int(delta.total_seconds()) * 1_000_000


NOISE_HISTORY = [
    # (url, title, visits, day/hour/min offsets across the last week)
    ("https://wiki.oe.internal/standup", "standup notes — wiki", 14, (2026, 3, 17, 9, 2)),
    ("https://wiki.oe.internal/printer-dock-4", "printer-dock-4 status (day 40)", 6, (2026, 3, 17, 9, 11)),
    ("https://jira.oe.internal/OE-2211", "OE-2211: toner procurement, escalated", 3, (2026, 3, 16, 14, 40)),
    ("https://jira.oe.internal/OE-2212", "OE-2212: toner procurement, re-escalated", 2, (2026, 3, 16, 16, 5)),
    ("https://wiki.oe.internal/q3-deck-draft", "Q3 deck draft v7 (FINANCE ONLY)", 1, (2026, 3, 17, 15, 22)),
    ("https://poster-gen.oe-demo.net/gallery", "poster-gen — recent posters", 9, (2026, 3, 15, 11, 30)),
    ("https://wiki.oe.internal/onboarding", "onboarding checklist", 2, (2026, 3, 13, 10, 0)),
    ("https://snacks.oe.internal/breakroom", "breakroom ledger", 21, (2026, 3, 17, 16, 45)),
    ("https://mail.oe.internal/search?q=toner", "mail search: toner", 4, (2026, 3, 17, 9, 30)),
    ("https://mail.oe.internal/search?q=%22badge%20ceremony%22", "mail search: badge ceremony", 1, (2026, 3, 17, 9, 41)),
    ("https://confluence.oe.internal/value-cards", "value cards — quarterly deck assets", 2, (2026, 3, 17, 10, 15)),
    ("https://time.oe.internal/", "what time is it (again)", 30, (2026, 3, 17, 8, 58)),
]

DELETED_ROWS = [
    (FLAG_URL, "badge ceremony flag (do not bookmark) (do not print)", 3,
     (2026, 3, 17, 9, 44)),
    ("https://wiki.oe.internal/q3-deck-draft?v=7&review=kevin", "Q3 deck v7 review notes", 1,
     (2026, 3, 17, 15, 40)),
    ("https://notes.oe.internal/u/k.okafor/drafts", "drafts (private)", 1,
     (2026, 3, 17, 9, 46)),
]

WIPE_REPORT = """\
IT-ASSET WIPE REPORT — LT-OE-0442 (returning contractor laptop)
operator: k.okafor            ticket: OE-2208            date: 2026-03-18

tool: browser "clear browsing data" (time range: all time)
cleared per the tool: browsing history, cookies, downloads
result reported by the tool: SUCCESS

notes:
  the browser was closed with the window X during step 3. the browser's
  own status page called this "ungraceful" and said the write-ahead log
  "was not checkpointed." checkpointing is best effort. best effort was
  achieved. we are moving on.

  the tool also notes it "does not manage the disk cache folder", which
  lives outside the profile folder the tool watches. this is documented
  vendor behavior and definitely not the reason we are attaching these
  files to the ticket.

spot check: history rows remaining = 0. wipe is clean. as clean as a
wipe gets, which is a phrase legal asked me to stop using.
"""

CACHE_WIKI = """HTTP/1.1 200 OK
Content-Type: text/plain

standup notes — week of 2013-08-19 (cache hit, 4h old)
* ledgerline migration still "in progress" (week 6)
* the printer is fine. the printer is not fine.
"""

CACHE_EARLY = """HTTP/1.1 200 OK
Content-Type: text/html

<!doctype html>
<html>
<head><title>early access — ordinary engineering</title></head>
<body>
<h1>early access</h1>
<p>You have been invited to the badge ceremony preview. Keep this link.
Do not share this link. Do not print this link. Legal is tired.</p>
<!-- the invite key doubles as the ceremony flag for the badge reader:
     {flag} -->
</body>
</html>
"""

CACHE_POSTER = """HTTP/1.1 200 OK
Content-Type: text/html

<!doctype html>
<html><head><title>poster-gen — gallery</title></head>
<body><h1>recent posters</h1><ul><li>index_no_1.webp</li><li>index_no_2.webp</li></ul>
</body></html>
"""

BOOKMARKS = {
    "roots": {
        "bookmark_bar": {
            "children": [
                {"name": "wiki", "url": "https://wiki.oe.internal/"},
                {"name": "printer-dock-4 status", "url": "https://wiki.oe.internal/printer-dock-4"},
                {"name": "kevin's reading list", "url": "https://notes.oe.internal/u/k.okafor/reading-list"},
            ],
            "name": "Bookmarks bar", "type": "folder",
        },
        "name": "Bookmarks bar", "type": "folder",
    },
    "version": 1,
}


def build_history(profile: str) -> None:
    db = os.path.join(profile, "History")
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA page_size=4096")
    con.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "url LONGVARCHAR, title LONGVARCHAR, visit_count INTEGER "
                "DEFAULT 0, typed_count INTEGER DEFAULT 0, "
                "last_visit_time INTEGER NOT NULL, hidden INTEGER DEFAULT 0)")
    con.execute("CREATE TABLE visits (id INTEGER PRIMARY KEY, "
                "url INTEGER NOT NULL, visit_time INTEGER NOT NULL, "
                "from_visit INTEGER, transition INTEGER DEFAULT 805306370)")
    for url, title, vc, when in NOISE_HISTORY:
        t = chrome_time(*when)
        cur = con.execute("INSERT INTO urls VALUES (NULL,?,?,?,0,?,0)",
                          (url, title, vc, t))
        con.execute("INSERT INTO visits VALUES (NULL,?,?,NULL,805306370)",
                    (cur.lastrowid, t))
    # the incident, right before the wipe
    for url, title, vc, when in DELETED_ROWS:
        t = chrome_time(*when)
        cur = con.execute("INSERT INTO urls VALUES (NULL,?,?,?,0,?,0)",
                          (url, title, vc, t))
        con.execute("INSERT INTO visits VALUES (NULL,?,?,NULL,805306370)",
                    (cur.lastrowid, t))
    con.commit()

    # the wipe: the tool deletes rows. the frames above (pre-deletion page
    # images) stay in the WAL — the browser is killed before any checkpoint.
    con.execute("DELETE FROM urls WHERE url = ?", (FLAG_URL,))
    con.execute("DELETE FROM urls WHERE url LIKE '%review=kevin%'")
    con.execute("DELETE FROM urls WHERE url LIKE '%/drafts'")
    con.commit()

    # snapshot exactly what the killed laptop had: db + wal, no shm.
    # copy to temp names first — con.close() checkpoints and removes the WAL.
    shutil.copy(db, db + ".snap")
    shutil.copy(db + "-wal", db + "-wal.snap")
    con.close()
    os.replace(db + ".snap", db)
    os.replace(db + "-wal.snap", db + "-wal")


def build_cache(profile: str) -> None:
    cache = os.path.join(profile, "Cache")
    os.makedirs(cache, exist_ok=True)
    # simple-cache v1-ish framing: 8-byte magic, then key/headers/body.
    # chrome parses the real thing; players get the same strings either way.
    magic = struct.pack("<Q", 0xFcfb6d1ba7725c30)
    for name, key, body in (
        ("f_000001", "https://wiki.oe.internal/standup", CACHE_WIKI),
        ("f_000002", f"https://early-access.oe-demo.net/?k={FLAG}", CACHE_EARLY.format(flag=FLAG)),
        ("f_000003", "https://poster-gen.oe-demo.net/gallery", CACHE_POSTER),
    ):
        with open(os.path.join(cache, name), "wb") as f:
            f.write(magic)
            f.write(struct.pack("<I", len(key)) + key.encode())
            f.write(struct.pack("<I", len(body)) + body.encode())

    with open(os.path.join(profile, "Bookmarks"), "w") as f:
        json.dump(BOOKMARKS, f, indent=2)


def main() -> None:
    shutil.rmtree(HANDOUT, ignore_errors=True)
    profile = os.path.join(HANDOUT, "profile")
    os.makedirs(profile)
    build_history(profile)
    build_cache(profile)
    with open(os.path.join(HANDOUT, "it_wipe_report.txt"), "w") as f:
        f.write(WIPE_REPORT)
    print("handout written to", os.path.normpath(HANDOUT))


if __name__ == "__main__":
    main()

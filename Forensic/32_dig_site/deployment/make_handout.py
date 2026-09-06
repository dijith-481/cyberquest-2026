#!/usr/bin/env python3
"""dig_site — deterministic handout generator.

Regenerates ../handout/skills_archive.zip: a real git repository of
"lost multiverse skills" whose entire history was backdated into the
1980s by a broken import script. The flag is NOT in any dangling commit.

The solve is a four-layer chain (see admin/solution.md):
  1. `git fsck` finds two decoy candidate imports and one receipt commit
     pointing at a "cold export" — the skill was moved to a pack.
  2. The pack sits in .git/objects/pack/ with NO .idx, so git ignores it
     entirely; the player must `git index-pack` it.
  3. The revived tip adds skills/spreadsheet_divination.md, but the flag
     blob was excluded from the pack — only its sha survives in the tree.
  4. The blob exists as a loose object with its zlib header stripped
     ("corrupt" to git); raw-inflating it yields the flag.

Nothing here is secret; the solve path is documented in admin/solution.md.
Requires git on PATH.
"""

import os
import shutil
import subprocess
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{g1t_fck_r3m3mb3rs_wh4t_br4nch3s_f0rg3t_d64b02}"

REPO_NAME = "skills_archive"
COLD_SKILL = "spreadsheet_divination"
COLD_TITLE = "Spreadsheet Divination"

README = """\
# skills_archive

Import of the pre-merger skill matrix into the new HR system.

Every import timestamp came out in the 1980s. The vendor says the dates
were "preserved from the source system." The source system was a spreadsheet.
The spreadsheet was written in 2024. Nobody wants to talk about it.

The archive was exported in pieces and reassembled by hand, on a machine
that "has never lost anything, technically." Housekeeping has been on the
backlog since the import. Several candidate imports never made it to a
branch. Ask fsck.

- skills/ — one file per skill, exactly as imported
"""

# (skill slug, title, body lines) — the visible, boring history
SKILLS = [
    ("alibi_weaving", "Alibi Weaving",
     ["STATUS: lost", "Practitioners could produce three mutually consistent",
      "accounts of the same afternoon. Deprecated after legal reviewed",
      "the concept of 'three'."]),
    ("arrow_sorting", "Arrow Sorting",
     ["STATUS: lost", "Sorted arrows by intent rather than by direction.",
      "Warehouse staff loved it. OSHA did not return our calls."]),
    ("budget_foresight", "Budget Foresight",
     ["STATUS: lost", "Forecasts next year's budget to the unit, then",
      "spends it anyway. Failed in every pilot. Kept in the archive",
      "for emotional reasons."]),
    ("cascade_napping", "Cascade Napping",
     ["STATUS: lost", "One nap propagates through the org chart. Peak",
      "documented efficiency: 11 departments, simultaneously."]),
    ("deadline_negotiation", "Deadline Negotiation",
     ["STATUS: lost", "Negotiates with deadlines directly. Deadlines are",
      "surprisingly reasonable when addressed respectfully."]),
    ("echo_filing", "Echo Filing",
     ["STATUS: lost", "Files documents in the past, so they arrive",
      "already overdue. Imported as-is. Nobody has used it. Correctly."]),
    ("furniture_persuasion", "Furniture Persuasion",
     ["STATUS: lost", "Convinces office furniture to stay put. Partially",
      "responsible for the good chairs in lobby B."]),
    ("gravity_scheduling", "Gravity Scheduling",
     ["STATUS: lost", "Schedules meetings at times when gravity is weaker.",
      "Attendance improved 4%. Statistically a rounding error. Kept."]),
    ("humidity_campaigning", "Humidity Campaigning",
     ["STATUS: lost", "Campaigns for office humidity by indirect means.",
      "The plant diary is the only surviving artifact and it is,",
      "frankly, more about the plants."]),
    ("implication_mowing", "Implication Mowing",
     ["STATUS: lost", "The lawn is mowed the moment someone implies it",
      "should be. Nobody knows who mows it. Do not investigate."]),
    ("journal_deflection", "Journal Deflection",
     ["STATUS: lost", "Redirects awkward questions into a journal that",
      "is then lost. The journal is never lost. That is the skill."]),
    ("keystroke_empathy", "Keystroke Empathy",
     ["STATUS: lost", "Feels which keys are pressed with intent and",
      "which are pressed with despair. QA refuses to be certified in it."]),
    ("ledger_divination", "Ledger Divination",
     ["STATUS: lost", "Reads next quarter's expenses in the smudge",
      "patterns of the current ledger. Accuracy: 61%. Which is still",
      "better than the deck."]),
    ("meeting_apport", "Meeting Apport",
     ["STATUS: lost", "Teleports a meeting to whoever is least prepared.",
      "Imported twice by mistake. Both copies work. Do not run both."]),
    ("nostalgia_throttling", "Nostalgia Throttling",
     ["STATUS: lost", "Caps how often anyone can say 'in the old universe",
      "we did it like this' to twice per standup. Enforcement lapsed."]),
    ("onboarding_shadowing", "Onboarding Shadowing",
     ["STATUS: lost", "The shadow shows up first and does the work.",
      "The new hire arrives to find everything done and one extra",
      "coffee mug. HR policy is silent on extra mugs."]),
    ("parking_orthodoxy", "Parking Orthodoxy",
     ["STATUS: lost", "Assigns parking by a formula nobody can parse.",
      "The formula was lost. The assignments continue anyway."]),
    ("quiet_hours_ritual", "Quiet Hours Ritual",
     ["STATUS: lost", "Two hours of enforced silence per week, observed",
      "by everyone including the printer. The printer observance is",
      "regarded as the most credible part."]),
    ("redundancy_pruning", "Redundancy Pruning",
     ["STATUS: lost", "Identifies work that duplicates other work and",
      "prunes it. Attempted on this very archive. Failed, obviously."]),
    ("standup_theurgy", "Standup Theurgy",
     ["STATUS: lost", "Summons a standup that already happened and asks",
      "it what it meant. Findings: 'blocked, spiritually.'"]),
    ("toner_communion", "Toner Communion",
     ["STATUS: lost", "Negotiates with printers as equals. The only skill",
      "on this list with documented success. Kevin teaches it informally."]),
    ("universal_remote", "Universal Remote",
     ["STATUS: lost", "One remote for every device in the building,",
      "including the building. Tested once. The building declined."]),
    ("vendetta_accounting", "Vendetta Accounting",
     ["STATUS: lost", "Tracks grudges as liabilities with amortization.",
      "Finance declined to adopt it and adopted it privately."]),
    ("wardrobe_bifurcation", "Wardrobe Bifurcation",
     ["STATUS: lost", "Splits a wardrobe across two universes so laundry",
      "is always done somewhere. Legal has questions. The questions",
      "are about the shirts, not the universes."]),
    ("year_zero_reconciliation", "Year Zero Reconciliation",
     ["STATUS: lost", "Reconciles books to a year that did not happen.",
      "The reconciliation balances. Nobody sleeps well after."]),
]

DANGLING = [
    # decoy 1: seductive wording, no flag
    ("candidate-import-1984a", "wip: crisis foresight",
     "crisis_foresight", "Crisis Foresight",
     ["STATUS: lost", "Sees crises two weeks out. The candidate import",
      "was abandoned when it kept seeing the same crisis and the crisis",
      "kept being 'this archive.' The recovery phrase for this entry was",
      "retired by legal and is not in this repository. Stop asking."]),
    # decoy 2: ASCII-art 'flag', no flag
    ("candidate-import-1985b", "import attempt 2",
     "flag_polishing", "Flag Polishing",
     ["STATUS: lost", "Polishes the office flag. The office flag is",
      "decorative and also, per facilities, 'not load-bearing.'",
      "", "  .-~-~-~-.",
      " /  FLAG   \\",
      " \\  ~~~~~  /",
      "  '-~-~-~-='", "",
      "The above is a drawing of the flag. It is not a flag. It is a",
      "drawing. Facilities would like this entry deleted."]),
    # breadcrumb: the receipt for the cold export
    ("candidate-import-1987c", "repack: cold export",
     None, None, None),  # handled specially in main()
]


def run(repo: str, *args: str, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, env=dict(os.environ),
                          check=check, capture_output=True, text=True)


def commit(repo: str, msg: str, when: str) -> str:
    run(repo, "add", "-A")
    env = dict(os.environ)
    env.update({"GIT_AUTHOR_DATE": f"{when} +0000",
                "GIT_COMMITTER_DATE": f"{when} +0000"})
    subprocess.run(["git", "commit", "-m", msg], cwd=repo, env=env,
                   check=True, capture_output=True, text=True)
    return run(repo, "rev-parse", "HEAD").stdout.strip()


def write_skill(repo: str, slug: str, title: str, body) -> None:
    d = os.path.join(repo, "skills")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{slug}.md"), "w") as f:
        f.write(f"# {title}\n\n" + "\n".join(body) + "\n")


def loose_object_path(repo: str, sha: str) -> str:
    return os.path.join(repo, ".git", "objects", sha[:2], sha[2:])


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)
    out_zip = os.path.join(HANDOUT, f"{REPO_NAME}.zip")
    if os.path.exists(out_zip):
        os.remove(out_zip)

    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, REPO_NAME)
        os.makedirs(repo)
        run(repo, "init", "-q", "-b", "main")
        run(repo, "config", "user.name", "skills-archive-import")
        run(repo, "config", "user.email", "import@ordinary.engineering")

        with open(os.path.join(repo, "README.md"), "w") as f:
            f.write(README)
        commit(repo, "import: seed the skills archive", "1984-01-09T09:14:00")

        # the visible history: one commit per skill, all backdated 1984-1989
        dates = ["1984-03-02T10:31:00", "1984-06-17T14:02:00", "1984-11-30T09:47:00",
                 "1985-02-08T11:20:00", "1985-05-19T16:55:00", "1985-08-04T08:03:00",
                 "1985-12-21T13:37:00", "1986-01-25T10:00:00", "1986-04-11T15:41:00",
                 "1986-07-07T09:09:00", "1986-10-30T12:12:00", "1987-02-14T17:26:00",
                 "1987-06-01T08:45:00", "1987-09-23T11:11:00", "1988-01-16T14:58:00",
                 "1988-05-05T10:26:00", "1988-08-19T09:33:00", "1988-11-11T16:04:00",
                 "1989-02-27T10:52:00", "1989-06-06T13:13:00", "1989-09-09T15:07:00",
                 "1989-12-31T23:59:00"]
        for i, (slug, title, body) in enumerate(SKILLS):
            write_skill(repo, slug, title, body)
            commit(repo, f"import: {slug}", dates[i % len(dates)])
            if i in (7, 15):
                run(repo, "update-ref", "refs/heads/archive-import", "HEAD")

        env = dict(os.environ)
        env.update({"GIT_COMMITTER_DATE": "1984-12-01T00:00:00",
                    "GIT_COMMITTER_NAME": "skills-archive-import",
                    "GIT_COMMITTER_EMAIL": "import@ordinary.engineering"})
        subprocess.run(["git", "tag", "-a", "-m", "archive import tag, do not move",
                        "v1984.0.1", "HEAD~20"], cwd=repo, env=env, check=True,
                       capture_output=True, text=True)

        # ------------------------------------------------ the cold export
        # a branch that never reached main: the skill was packed for cold
        # storage, but the pack ships WITHOUT its .idx (git ignores it) and
        # the final calibration blob was never packed at all — it survives
        # only as a damaged loose object (zlib header stripped).
        run(repo, "checkout", "-q", "-b", "cold-export")
        write_skill(repo, COLD_SKILL, COLD_TITLE,
                    ["STATUS: cold", "Placeholder row. Calibration pending."])
        c1 = commit(repo, "cold: import spreadsheet divination (stub)",
                    "1988-06-06T06:06:00")
        write_skill(repo, COLD_SKILL, COLD_TITLE,
                    ["STATUS: cold", "Reads future revenue in the cell borders of",
                     "the Q3 workbook. The calibration phrase is stored with",
                     "the cold copy of this file. If you are reading the stub,",
                     "you found the pack. Now find what the pack forgot.",
                     "",
                     f"calibration phrase: {FLAG}"])
        c2 = commit(repo, "cold: calibrate", "1988-06-06T06:41:00")

        blob_sha = run(repo, "ls-tree", "-r", c2,
                       "--", f"skills/{COLD_SKILL}.md").stdout.split()[2]

        # pack EVERYTHING reachable from c2 except the final blob
        objs = run(repo, "rev-list", "--objects", c2).stdout.splitlines()
        shas = [line.split()[0] for line in objs if line.split()[0] != blob_sha]
        p = subprocess.run(["git", "pack-objects", "--quiet",
                            os.path.join(repo, ".git", "objects", "pack", "pack")],
                           cwd=repo, check=True, input="\n".join(shas) + "\n",
                           capture_output=True, text=True)
        pack_base = p.stdout.strip()          # the pack checksum
        pack_name = f"pack-{pack_base}.pack"
        pack_path = os.path.join(repo, ".git", "objects", "pack", pack_name)
        idx_path = pack_path[:-5] + ".idx"
        os.remove(idx_path)                   # "the idx went with the courier"
        rev_path = pack_path + ".rev"
        if os.path.exists(rev_path):
            os.remove(rev_path)               # the courier took this one too

        # the cold commits/trees must live ONLY in the pack: drop their
        # loose copies, or `git cat-file` would work without indexing it.
        # only objects NEW to this branch may be removed — rev-list from
        # c2 also lists everything main already has (its trees must stay).
        main_shas = {line.split()[0]
                     for line in run(repo, "rev-list", "--objects", "main")
                     .stdout.splitlines()}
        new_shas = [line.split()[0] for line in objs
                    if line.split()[0] not in main_shas]
        for sha in new_shas:
            if sha == blob_sha:
                continue
            typ = run(repo, "cat-file", "-t", sha).stdout.strip()
            if typ in ("commit", "tree"):
                lp = loose_object_path(repo, sha)
                if os.path.exists(lp):
                    os.remove(lp)
        # the final blob's ONLY copy becomes a damaged loose object:
        # strip the 2-byte zlib header, keep the raw deflate payload
        lp = loose_object_path(repo, blob_sha)
        raw = open(lp, "rb").read()
        if raw[:1] != b"\x78":
            raise SystemExit("unexpected loose object compression")
        os.chmod(lp, 0o644)
        open(lp, "wb").write(raw[2:])

        run(repo, "checkout", "-q", "main")
        run(repo, "branch", "-q", "-D", "cold-export")

        # the receipt dangling commit points at the cold export
        run(repo, "checkout", "-q", "-b", "candidate-import-1987c")
        with open(os.path.join(repo, "cold_storage_receipt.txt"), "w") as f:
            f.write(
                "cold storage receipt — export 1989-47\n\n"
                f"shipped:        .git/objects/pack/{pack_name}\n"
                f"not shipped:    .git/objects/pack/{pack_name[:-5]}.idx\n"
                "contents:       skills/spreadsheet_divination.md, calibration\n"
                "                included, plus the import history behind it\n\n"
                "note from the reassembly bench: the pack lives at the bottom\n"
                "of objects/. git will not look at it until its index comes\n"
                "home. the courier has not come home either. one of the files\n"
                "inside was 'handled firmly' by the courier's bag. we shipped\n"
                "it anyway. we ship everything. that is the whole problem.\n")
        commit(repo, "repack: cold export", "1988-07-07T07:07:00")
        run(repo, "checkout", "-q", "main")
        run(repo, "branch", "-q", "-D", "candidate-import-1987c")

        # two decoy candidate imports (loose, dangling, also 1980s)
        for tag, msg, slug, title, body in DANGLING[:2]:
            run(repo, "checkout", "-q", "-b", tag)
            write_skill(repo, slug, title, body)
            commit(repo, msg, "1985-03-13T13:31:00")
            run(repo, "checkout", "-q", "main")
            run(repo, "branch", "-q", "-D", tag)

        # the export lost the reflogs — without them fsck reports the
        # abandoned candidate imports as dangling
        shutil.rmtree(os.path.join(repo, ".git", "logs"), ignore_errors=True)

        # ------------------------------------------------------ sanity
        if not os.path.exists(pack_path) or os.path.exists(idx_path):
            raise SystemExit("pack shipped without idx, or idx still present")
        # the flag must be greppable NOWHERE in plain form
        reachable = subprocess.run(
            ["git", "grep", FLAG, "main", "archive-import"], cwd=repo,
            capture_output=True, text=True)
        if reachable.returncode == 0:
            raise SystemExit("flag reachable from a branch")
        pack_bytes = open(pack_path, "rb").read()
        if FLAG.encode() in pack_bytes:
            raise SystemExit("flag appears in plaintext inside the pack")
        # git must consider the final blob broken
        probe = run(repo, "cat-file", "-p", blob_sha, check=False)
        if probe.returncode == 0:
            raise SystemExit("damaged blob still parses as an object")
        fsck = run(repo, "fsck", "--unreachable", check=False)
        out = fsck.stdout + fsck.stderr
        if out.count("unreachable commit") < 3:
            raise SystemExit(f"expected >=3 unreachable commits, got: {out!r}")
        if "corrupt" not in out and blob_sha not in out:
            raise SystemExit("fsck does not flag the damaged blob")
        # the cold commits must NOT be readable without the idx
        cold = run(repo, "cat-file", "-p", c2, check=False)
        if cold.returncode == 0:
            raise SystemExit("cold commit readable without indexing the pack")
        # raw inflation of the damaged blob must yield the flag
        payload = zlib.decompressobj(-15).decompress(open(loose_object_path(repo, blob_sha), "rb").read())
        if FLAG.encode() not in payload:
            raise SystemExit(f"raw inflate does not recover the flag: {payload!r}")
        if os.path.exists(os.path.join(repo, ".git", "lost-found")):
            raise SystemExit("fsck wrote .git/lost-found — do not ship that")

        # ------------------------------------------------------ package
        shutil.make_archive(out_zip[:-4], "zip", tmp, REPO_NAME)

    print("handout written to", os.path.normpath(out_zip))


if __name__ == "__main__":
    main()

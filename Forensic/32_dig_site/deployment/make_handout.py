#!/usr/bin/env python3
"""dig_site — deterministic handout generator.

Regenerates ../handout/skills_archive.zip: a real git repository of
"lost multiverse skills" whose entire history was backdated into the
1980s by a broken import script. The visible branches are noise. The
interesting objects are unreachable — findable only via `git fsck`.

Nothing here is secret; the solve path is documented in admin/solution.md.
Requires git on PATH.
"""

import os
import shutil
import subprocess
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{g1t_fck_r3m3mb3rs_wh4t_br4nch3s_f0rg3t_d64b02}"

REPO_NAME = "skills_archive"

README = """\
# skills_archive

Import of the pre-merger skill matrix into the new HR system.

Every import timestamp came out in the 1980s. The vendor says the dates
were "preserved from the source system." The source system was a spreadsheet.
The spreadsheet was written in 2024. Nobody wants to talk about it.

Import ran from `archive-import`. The main branch was fast-forwarded after
legal reviewed "the wording." Several candidate imports never made it to a
branch. Housekeeping has been on the backlog since the import.

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

# Unreachable candidate imports. The first two are decoys; the third one
# is real and deliberately boring-looking.
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
    # the real one: boring message, boring name, flag mid-prose
    ("candidate-import-1984c", "rebase cleanup",
     "spreadsheet_divination", "Spreadsheet Divination",
     ["STATUS: lost", "Reads future revenue in the cell borders of the",
      f"Q3 workbook. Calibration phrase: {FLAG}",
      "The phrase is for calibration only. Finance insists it is 'not a",
      "secret, just load-bearing.' The borders it was read from have",
      "since been reformatted. The skill survives in import form only."]),
]


def run(repo: str, *args: str, env_extra=None) -> None:
    env = dict(os.environ)
    env.update(env_extra or {})
    subprocess.run(["git", *args], cwd=repo, env=env, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def commit(repo: str, tree: str, msg: str, when: str) -> None:
    run(repo, "add", "-A")
    date_env = {"GIT_AUTHOR_DATE": f"{when} +0000",
                "GIT_COMMITTER_DATE": f"{when} +0000"}
    run(repo, "commit", "-m", msg, env_extra=date_env)


def author_env(i: int) -> dict:
    names = [("Okonkwo, S.", "s.okonkwo"), ("Marchetti, D.", "d.marchetti"),
             ("Vale, M.", "m.vale"), ("Okafor, K.", "k.okafor"),
             ("Underwood, K.", "k.underwood")]
    name, email = names[i % len(names)]
    return {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": f"{email}@ordinary.engineering",
            "GIT_COMMITTER_NAME": "skills-archive-import",
            "GIT_COMMITTER_EMAIL": "import@ordinary.engineering"}


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
        commit(repo, ".", "import: seed the skills archive", "1984-01-09T09:14:00")

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
            d = os.path.join(repo, "skills")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f"{slug}.md"), "w") as f:
                f.write(f"# {title}\n\n" + "\n".join(body) + "\n")
            commit(repo, ".", f"import: {slug}", dates[i % len(dates)])
            run(repo, "update-ref", "refs/heads/archive-import", "HEAD") \
                if i in (7, 15) else None

        # a tag nobody updated, pointing mid-history
        run(repo, "tag", "-a", "-m", "archive import tag, do not move",
            "v1984.0.1", "HEAD~20",
            env_extra={"GIT_COMMITTER_DATE": "1984-12-01T00:00:00",
                       "GIT_COMMITTER_NAME": "skills-archive-import",
                       "GIT_COMMITTER_EMAIL": "import@ordinary.engineering"})

        # candidate imports that never reached a branch (dangling commits)
        for tag, msg, slug, title, body in DANGLING:
            run(repo, "checkout", "-q", "-b", tag)
            d = os.path.join(repo, "skills")
            with open(os.path.join(d, f"{slug}.md"), "w") as f:
                f.write(f"# {title}\n\n" + "\n".join(body) + "\n")
            commit(repo, ".", msg, "1985-03-13T13:31:00")
            run(repo, "checkout", "-q", "main")
            run(repo, "branch", "-q", "-D", tag)

        # the export that produced this archive lost the reflogs (housekeeping
        # or a bad tar, nobody remembers) — without them fsck reports the
        # abandoned candidate imports as dangling
        shutil.rmtree(os.path.join(repo, ".git", "logs"), ignore_errors=True)

        # sanity: the flag must be unreachable from every ref
        reachable = subprocess.run(
            ["git", "grep", FLAG, "main", "archive-import"], cwd=repo,
            capture_output=True, text=True)
        if reachable.returncode == 0:
            raise SystemExit("flag is reachable from a branch — it should not be")
        fsck = subprocess.run(["git", "fsck", "--unreachable"], cwd=repo,
                              capture_output=True, text=True).stdout
        if fsck.count("unreachable commit") < 3:
            raise SystemExit(f"expected >=3 dangling commits, fsck said: {fsck!r}")
        # --unreachable must not have written anything; double-check no
        # lost-found directory ever lands in the handout
        if os.path.exists(os.path.join(repo, ".git", "lost-found")):
            raise SystemExit("fsck wrote .git/lost-found — do not ship that")

        # package the whole repo (loose objects included, no gc)
        base = os.path.basename(out_zip)
        shutil.make_archive(out_zip[:-4], "zip", tmp, REPO_NAME)

    print("handout written to", os.path.normpath(out_zip))


if __name__ == "__main__":
    main()

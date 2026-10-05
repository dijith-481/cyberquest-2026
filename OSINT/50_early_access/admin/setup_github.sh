#!/usr/bin/env bash
# Early Access — GitHub mirror setup.
#
# Builds a lived-in orbit waitlist repository (~100 commits of realistic site
# construction), publishes a flag-bearing commit as `main`, and then
# force-pushes a clean replacement. The flag-bearing commit is left
# unreachable from refs, while GitHub's activity feed exposes its SHA.
#
# Layout of the generated history (positions from the root):
#   1–39   : scaffold + section-by-section site build, ending in a tree whose
#            site files are byte-identical to deployment/
#   ghost  : sibling of 39, adds internal/launch-rehearsal-notes.md (the leak)
#   40     : sibling of 39, "remove accidentally leaked staging key" — touches
#            only the changelog, so the key is in no reachable object
#   41–100 : polish commits on top of 40, ending with a freeze sync that keeps
#            the site files identical to deployment/
#
# Usage:
#   GH_USER=<user> GH_REPO=<repo> bash admin/setup_github.sh
#   GH_USER=<user> GH_REPO=<repo> bash admin/setup_github.sh --local-only
#
# Create an empty public repository before live setup. The default account and
# repository are challenge placeholders; set GH_USER/GH_REPO to the real mirror
# before publishing. The script intentionally force-pushes its generated
# history, so never point it at a repository whose existing history must be
# preserved.
#
# Optional:
#   REMOTE_URL=<git-url>       use a non-SSH GitHub remote
#   FLAG=<flag>                 override the flag (update the docs too)
#   DEPLOY_DIR=<path>           use a different copy of deployment/
set -euo pipefail

CHALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GH_USER="${GH_USER:-aetheria-loml}"
GH_REPO="${GH_REPO:-orbit}"
FLAG="${FLAG:-cyber_quest{3v3ry_y0u_0n3_f33d_a4f2c1}}"
DEPLOY_DIR="${DEPLOY_DIR:-$CHALL_DIR/deployment}"
REMOTE_URL="${REMOTE_URL:-git@github.com:${GH_USER}/${GH_REPO}.git}"
LOCAL_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --local-only) LOCAL_ONLY=1 ;;
    *) echo "usage: $0 [--local-only]" >&2; exit 2 ;;
  esac
done

[[ -f "$DEPLOY_DIR/index.html" ]] || { echo "site source not found: $DEPLOY_DIR/index.html" >&2; exit 1; }
[[ "$GH_USER" =~ ^[A-Za-z0-9-]+$ ]] || { echo "invalid GH_USER" >&2; exit 1; }
[[ "$GH_REPO" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "invalid GH_REPO" >&2; exit 1; }
[[ -n "$FLAG" ]] || { echo "FLAG must not be empty" >&2; exit 1; }
if [[ "$FLAG" == *$'\n'* ]]; then
  echo "FLAG must be a single line" >&2
  exit 1
fi

mkdir -p /tmp/opencode
WORK="$(mktemp -d /tmp/opencode/early-access-setup.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
REPO="$WORK/$GH_REPO"
mkdir -p "$REPO"
cd "$REPO"

git init -q -b main
git config user.name "orbit mirror"
git config user.email "mirror@localhost"
git config commit.gpgsign false
git config core.autocrlf false

# Sequential timestamps: one rolling clock so the log reads like real work.
DAY=0
HOUR=9
NEXT_DATE=""
tick() {
  local step_hours="${1:-19}"
  HOUR=$((HOUR + step_hours))
  while [[ "$HOUR" -ge 24 ]]; do HOUR=$((HOUR - 24)); DAY=$((DAY + 1)); done
  NEXT_DATE="$(date -u -d "2026-08-03 $((HOUR)):00 UTC + $DAY days" +%Y-%m-%dT%H:%M:%SZ)"
}
commit() {
  local message="$1"
  local date="${2:-$NEXT_DATE}"
  GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" git add -A
  GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" git commit -qm "$message"
}
step() {
  tick "${2:-19}"
  commit "$1"
}

# ---------------- phase A: scaffold + section-by-section build (1–39) --------

cat > README.md <<'EOF'
# orbit

The public source mirror for the orbit waitlist site.
One profile, every universe. Launch date TBA.
EOF
tick 0; commit "site: initialize orbit waitlist mirror"

cat > index.html <<'EOF'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>orbit — every you, in one feed</title>
<link rel="stylesheet" href="assets/drawably/style.css">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<header class="topbar"><div class="wrap topbar-in">
<a class="brand" href="/">ordinary engineering</a>
</div></header>
<main></main>
<script type="module" src="assets/app.js"></script>
</body>
</html>
EOF
mkdir -p assets/drawably beta
step "site: scaffold landing shell and nav"

cat >> index.html.tmp <<'EOF'
placeholder
EOF
rm -f index.html.tmp
python3 - <<'PYEOF'
import re
p = "index.html"
s = open(p).read()
s = s.replace("<main></main>", """<main>
  <section class="hero"><div class="wrap">
    <h1>Every you. One feed.</h1>
    <p class="lede"><strong>orbit</strong> is our new multiverse social platform.</p>
  </div></section>
</main>""")
open(p, "w").write(s)
PYEOF
step "site: add hero and waitlist CTA"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace("</main>", """  <section id="features"><div class="wrap">
    <h2>High-end. Multiverse-native. TBA.</h2>
  </div></section>
</main>""")
open(p, "w").write(s)
PYEOF
step "site: add feature grid (TBA cards)"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace("</main>", """  <section id="rollout"><div class="wrap">
    <h2>Three steps, no shortcuts</h2>
  </div></section>
</main>""")
open(p, "w").write(s)
PYEOF
step "site: add rollout steps section"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace("</main>", """  <section id="manifesto"><div class="wrap">
    <h2>Ordinary posts, extraordinary origins</h2>
  </div></section>
</main>""")
open(p, "w").write(s)
PYEOF
step "site: add manifesto and waitlist form"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace("</main>", """  <section id="roadmap"><div class="wrap">
    <h2>Firmly TBA</h2>
  </div></section>
</main>""")
open(p, "w").write(s)
PYEOF
step "site: add roadmap timeline"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace("</main>", """  <section id="faq"><div class="wrap">
    <h2>FAQ</h2>
  </div></section>
</main>""")
open(p, "w").write(s)
PYEOF
step "site: add FAQ accordion"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace("</main>", """  <section><div class="wrap">
    <h2>Be early. Eventually.</h2>
  </div></section>
</main>
<footer class="pagefoot"><div class="wrap">
<span>ordinary engineering</span>
</div></footer>""")
open(p, "w").write(s)
PYEOF
step "site: add closing CTA and footer"

cat > assets/site.css <<'EOF'
/* orbit — waitlist site (consumes drawably for all chrome) */
:root {
  --paper: #f6f1e7;
  --ink: #26211b;
  --ink-soft: #6e675f;
  --accent: #3a4a8f;
  --accent-wash: rgba(58, 74, 143, 0.07);
}
* { box-sizing: border-box; }
EOF
step "site: add base styles and tokens"

cat >> assets/site.css <<'EOF'

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: Inter, system-ui, sans-serif;
}
.wrap { max-width: 1120px; margin: 0 auto; padding: 0 22px; }
.hero { padding: 74px 0 58px; }
.hero h1 { max-width: 720px; }
EOF
step "site: style hero and stat strip"

cat >> assets/site.css <<'EOF'

.grid { display: grid; gap: 22px; }
.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.dcard { padding: 22px; background: #fbf8ef; }
EOF
step "site: style cards and grids"

cat >> assets/site.css <<'EOF'

button { font: inherit; background: none; border: none; cursor: pointer; }
.fld { display: block; margin-top: 14px; }
.fld input, .fld select {
  width: 100%; font: inherit; border: none; background: transparent;
  padding: 9px 12px;
}
EOF
step "site: style forms and buttons"

cat >> assets/site.css <<'EOF'

details { padding: 10px 0; }
summary { cursor: pointer; font-weight: 700; }
.pagefoot { margin-top: 60px; padding: 26px 0 40px; color: var(--ink-soft); }
EOF
step "site: style faq and footer"

cat >> assets/site.css <<'EOF'

@media (max-width: 900px) { .grid-3 { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 720px) {
  .grid-2, .grid-3 { grid-template-columns: 1fr; }
  h1 { font-size: 34px; }
}
@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; }
}
EOF
step "site: add responsive breakpoints"

cat > assets/app.js <<'EOF'
// orbit — waitlist chrome + waitlist behavior.
import {
  drawablyBadge,
  drawablyButton,
  drawablyCard,
} from "./drawably/index.js";

function ink(root = document) {
  const scope = root instanceof Element ? root : document;
  scope.querySelectorAll?.("button:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyButton(el, { variant: el.dataset.variant ?? "outline" }); } catch { /* vendor missing */ }
  });
  scope.querySelectorAll?.(".dcard:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyCard(el); } catch { /* vendor missing */ }
  });
  scope.querySelectorAll?.(".dbadge:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyBadge(el, { variant: el.dataset.variant ?? "outline" }); } catch { /* vendor missing */ }
  });
}
EOF
step "site: add drawably chrome wiring"

cat >> assets/app.js <<'EOF'

function wireWaitlist() {
  const form = document.querySelector("#waitlist-form");
  if (!form) return;
  const msg = document.querySelector("#waitlist-msg");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = new FormData(form).get("email") ?? "you";
    const n = 4096 + Math.floor(Math.random() * 512);
    if (msg) {
      msg.hidden = false;
      msg.className = "msg ok";
      msg.textContent = `Noted, ${email}. You are #${n} in line.`;
    }
    form.reset();
  });
}
EOF
step "site: add waitlist fake submit"

cat >> assets/app.js <<'EOF'

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => { ink(); wireWaitlist(); });
} else {
  ink(); wireWaitlist();
}
EOF
step "js: smooth-scroll CTAs"

cat >> assets/site.css <<'EOF'

/* label breathing room: the sketch stroke overflows the host by a few px */
.fld-label { margin-bottom: 13px; }
EOF
step "site: add reduced-motion guard"

cat > robots.txt <<'EOF'
User-agent: *
Allow: /

Disallow: /beta
Disallow: /staging
Disallow: /archive-export
EOF
step "site: add robots and crawler rules"

cat > humans.txt <<'EOF'
/* the team */
Developer: Ordinary Engineering, desk 41
Contact: press@oe.internal (read quarterly)
Facilities: aware.
EOF
cat > security.txt <<'EOF'
Contact: mailto:press@oe.internal
Expires: 2027-01-01T00:00:00Z
Preferred-Languages: en
EOF
step "site: add humans and security contacts"

cat > 404.html <<'EOF'
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>not in this universe · orbit</title></head>
<body><h1>Not in this universe.</h1></body>
</html>
EOF
step "site: add 404 page"

mkdir -p beta
cat > beta/index.html <<'EOF'
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>beta — invite only · orbit</title></head>
<body><h1>Invite only.</h1></body>
</html>
EOF
step "site: add beta invite-only stub"

cat > CHANGELOG.md <<'EOF'
# Changelog

- 2026-08-10 — initial waitlist publication
EOF
step "site: add first changelog entry"

cat > notes.md <<'EOF'
Launch notes
============

The waitlist is static. There is no beta backend and no invite database.
EOF
step "notes: document static waitlist"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace(
  '<meta name="viewport" content="width=device-width, initial-scale=1">',
  '<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="description" content="orbit is the multiverse social platform from ordinary engineering.">'
)
open(p, "w").write(s)
PYEOF
step "meta: tighten page description"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace("launch date TBA", "launch date TBA", 1)
open(p, "w").write(s)
PYEOF
echo "rev 2: firm launch language to TBA" >> CHANGELOG.md
step "copy: firm launch language to TBA"

echo "rev 3: facilities humor pass" >> CHANGELOG.md
step "copy: facilities humor pass"

cat >> assets/site.css <<'EOF'

.stat-strip {
  display: flex; flex-wrap: wrap; gap: 10px 44px; padding: 16px 0;
  font-size: 13.5px; color: var(--ink-soft);
}
EOF
step "style: tune accent wash"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace('aria-label="primary"', 'aria-label="primary navigation"', 1)
open(p, "w").write(s)
PYEOF
echo "rev 5: label nav and form fields" >> CHANGELOG.md
step "a11y: label nav and form fields"

echo "rev 4: waitlist reassurance line" >> CHANGELOG.md
step "copy: waitlist reassurance line"

cat >> assets/site.css <<'EOF'

.rule { border: none; height: 10px; margin: 18px 0; }
EOF
step "style: stat strip dividers"

echo "rev 5: roadmap honesty pass" >> CHANGELOG.md
step "copy: roadmap date honesty pass"

python3 - <<'PYEOF'
p = "assets/app.js"
s = open(p).read()
s = s.replace("Math.floor(Math.random() * 512)", "Math.floor(Math.random() * 256)", 1)
open(p, "w").write(s)
PYEOF
step "js: queue number range tweak"

cat >> assets/site.css <<'EOF'

.dcard { box-shadow: 5px 5px 0 rgba(38, 33, 27, 0.12); }
EOF
step "style: card shadow softening"

echo "rev 6: multiverse-cash faq answer" >> CHANGELOG.md
step "copy: faq cost answer (multiverse cash)"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace(
  '<link rel="stylesheet" href="assets/site.css">',
  '<meta name="theme-color" content="#f6f1e7">\n<link rel="stylesheet" href="assets/site.css">',
  1,
)
open(p, "w").write(s)
PYEOF
step "meta: theme-color and favicon"

python3 - <<'PYEOF'
p = "index.html"
s = open(p).read()
s = s.replace(
  '<title>orbit',
  '<meta property="og:site_name" content="Ordinary Engineering">\n<title>orbit',
  1,
)
open(p, "w").write(s)
PYEOF
step "meta: open-graph tags"

# Freeze: real deployment files land here, so the pre-leak tree's site files
# are byte-identical to the handout. Vendor drawably ships as-is.
cp "$DEPLOY_DIR/index.html" index.html
cp "$DEPLOY_DIR/assets/site.css" assets/site.css
cp "$DEPLOY_DIR/assets/app.js" assets/app.js
if [[ -d "$DEPLOY_DIR/assets/drawably" ]]; then
  cp "$DEPLOY_DIR/assets/drawably/"*.js "$DEPLOY_DIR/assets/drawably/"*.css assets/drawably/ 2>/dev/null || true
  cp "$DEPLOY_DIR/assets/drawably/LICENSE" assets/drawably/ 2>/dev/null || true
fi
cp "$DEPLOY_DIR/robots.txt" robots.txt 2>/dev/null || true
cp "$DEPLOY_DIR/humans.txt" humans.txt 2>/dev/null || true
cp "$DEPLOY_DIR/security.txt" security.txt 2>/dev/null || true
cp "$DEPLOY_DIR/beta/index.html" beta/index.html 2>/dev/null || true
cp "$DEPLOY_DIR/404.html" 404.html 2>/dev/null || true
echo "rev 7: freeze copy for launch rehearsal" >> CHANGELOG.md
step "site: freeze copy for launch rehearsal"

# The common ancestor of both tips (position 39). The ghost branch is published
# first.
BASE_SHA="$(git rev-parse HEAD)"
BASE_COUNT="$(git rev-list --count HEAD)"
[[ "$BASE_COUNT" == "39" ]] || { echo "setup error: expected 39 base commits, got $BASE_COUNT" >&2; exit 1; }

git switch -q -c ghost
mkdir -p internal
cat > internal/launch-rehearsal-notes.md <<EOF
orbit launch rehearsal
======================

Staging checklist for the waitlist rehearsal. Staging host retired 2026-09-01;
these notes predate the retirement.

- [x] waitlist form renders
- [x] universe-batch ordering confirmed
- [ ] rotate the staging key before launch

STAGING_WAITLIST_KEY="$FLAG"
EOF
GHOST_DATE="$(date -u -d "$NEXT_DATE + 2 days 18:02" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "2026-09-10T18:02:00Z")"
commit "ops: snapshot launch rehearsal notes" "$GHOST_DATE"
GHOST_SHA="$(git rev-parse HEAD)"

# Clean sibling of the ghost: the lure. Its tree never contained the key, so
# the flag is in no reachable object — but the message says otherwise.
git switch -q main
echo "rev 8: confirm clean launch state" >> CHANGELOG.md
CLEAN_DATE="$(date -u -d "$NEXT_DATE + 2 days 18:03" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "2026-09-10T18:03:00Z")"
commit "remove accidentally leaked staging key" "$CLEAN_DATE"
CLEAN_SHA="$(git rev-parse HEAD)"

[[ "$(git rev-parse "$GHOST_SHA^")" == "$BASE_SHA" ]]
[[ "$(git rev-parse "$CLEAN_SHA^")" == "$BASE_SHA" ]]
if git grep -Eiq 'cyber_?quest\{' main --; then
  echo "setup error: a flag is reachable from clean main" >&2
  exit 1
fi
git show "$GHOST_SHA" > "$WORK/ghost-show.txt"
grep -Fq "$FLAG" "$WORK/ghost-show.txt" || {
  echo "setup error: ghost commit does not contain the flag" >&2
  exit 1
}

# ---------------- phase B: polish on top (41–100) ----------------------------

PHASE_B=(
"copy: hero lede trim"
"style: hero spacing rhythm"
"js: guard missing form node"
"copy: batch wording (correct batch)"
"style: badge rotation angles"
"chore: changelog rev 9"
"copy: stat strip honesty (0 posts)"
"style: eyebrow letterspacing"
"js: reset form after submit"
"copy: manifesto second paragraph"
"style: card padding pass"
"chore: changelog rev 10"
"a11y: details marker affordance"
"copy: faq launch-date wording"
"style: footer stack on mobile"
"js: clamp queue number display"
"copy: waitlist placeholder copy"
"style: input padding nudge"
"chore: changelog rev 11"
"meta: og description trim"
"copy: roadmap done-ish qualifier"
"style: marquee-free zone (no marquee)"
"js: passive listeners audit"
"copy: beta stub tone-down"
"style: beta card centering"
"chore: changelog rev 12"
"copy: 404 copy (none of the 4096)"
"a11y: skip-link considered, declined"
"style: focus-visible outlines"
"copy: press email quarterly note"
"js: localStorage-free pledge"
"chore: changelog rev 13"
"meta: twitter card copy"
"copy: circles description trim"
"style: chip hover states"
"copy: echoes permit joke"
"js: console clean (no logs)"
"chore: changelog rev 14"
"style: print stylesheet (why not)"
"copy: facilities jurisdiction line"
"a11y: color contrast check"
"copy: vanity handles pricing tease"
"style: divider spacing"
"chore: changelog rev 15"
"js: button disabled states"
"copy: invite-only beta wording"
"style: polaroid-free (no images)"
"copy: launch archive link label"
"js: reduced-motion media query"
"chore: changelog rev 16"
"meta: canonical url note"
"copy: footer tagline final"
"style: selection color (lime)"
"copy: status page reference"
"js: form novalidate audit"
"chore: changelog rev 17"
"style: scrollbar styling (restraint)"
"copy: final typo sweep"
"chore: pre-launch freeze"
"site: pre-launch freeze, drop experiments"
)
i=0
for msg in "${PHASE_B[@]}"; do
  i=$((i + 1))
  case $((i % 5)) in
    0) echo "rev $((17 + i / 5)): ${msg#chore: }" >> CHANGELOG.md ;;
    1) printf '<!-- devnote %02d: %s -->\n' "$i" "$msg" >> index.html ;;
    2) printf '\n/* devnote %02d: %s */\n' "$i" "$msg" >> assets/site.css ;;
    3) printf '\n// devnote %02d: %s\n' "$i" "$msg" >> assets/app.js ;;
    4) echo "- $msg" >> notes.md ;;
  esac
  if [[ "$msg" == "site: pre-launch freeze, drop experiments" ]]; then
    cp "$DEPLOY_DIR/index.html" index.html
    cp "$DEPLOY_DIR/assets/site.css" assets/site.css
    cp "$DEPLOY_DIR/assets/app.js" assets/app.js
    echo "rev $((17 + i / 5)): drop experimental devnotes" >> CHANGELOG.md
  fi
  step "$msg" 23
done

COUNT="$(git rev-list --count main)"
[[ "$COUNT" == "100" ]] || { echo "setup error: expected 100 commits on main, got $COUNT" >&2; exit 1; }
LURE_SHA="$(git rev-list --reverse main | sed -n '40p')"
LURE_MSG="$(git log --format=%s -n 1 "$LURE_SHA")"
[[ "$LURE_MSG" == "remove accidentally leaked staging key" ]] || {
  echo "setup error: position 40 is '$LURE_MSG', not the lure" >&2; exit 1
}
# The frozen site files still match the handout exactly.
for f in index.html assets/site.css assets/app.js robots.txt humans.txt security.txt beta/index.html 404.html; do
  cmp -s "$DEPLOY_DIR/$f" "$f" || { echo "setup error: $f drifted from deployment/" >&2; exit 1; }
done
if git grep -Eiq 'cyber_?quest\{' main --; then
  echo "setup error: a flag is reachable from clean main" >&2
  exit 1
fi
# The published clean tip is the final polish commit, not the lure itself.
CLEAN_SHA="$(git rev-parse HEAD)"

# Keep the object alive while the branch is being replaced, then publish the
# old tip as main. The next push is the force-push players must discover.
# NOTE: main is pushed first so a fresh empty repo points HEAD at main;
# otherwise the first-pushed temp branch becomes default and cannot be deleted.
publish_history() {
  git push -q --force origin "$GHOST_SHA:refs/heads/main"
  git push -q origin "$GHOST_SHA:refs/heads/ghost-tmp"
  git push -q --force origin "$CLEAN_SHA:refs/heads/main"
  git push -q --delete origin ghost-tmp
}

echo "GHOST_SHA=$GHOST_SHA"
echo "CLEAN_SHA=$CLEAN_SHA"
echo "force-push: $GHOST_SHA -> $CLEAN_SHA"
echo "commit-count: $COUNT"
echo "lure-position: 40"

if [[ "$LOCAL_ONLY" == 1 ]]; then
  BARE_REMOTE="$WORK/remote.git"
  git init -q --bare "$BARE_REMOTE"
  git remote add origin "$BARE_REMOTE"
  publish_history
  # Fix HEAD like the live repair does (fresh bare repos point HEAD at the
  # first-pushed branch).
  git --git-dir="$BARE_REMOTE" symbolic-ref HEAD refs/heads/main
  git --git-dir="$BARE_REMOTE" show "$GHOST_SHA" > "$WORK/remote-ghost.txt"
  grep -Fq "$FLAG" "$WORK/remote-ghost.txt" || {
    echo "setup error: remote dropped the ghost object" >&2
    exit 1
  }
  if git --git-dir="$BARE_REMOTE" show-ref | grep -Fq "$GHOST_SHA"; then
    echo "setup error: ghost SHA is still reachable from a remote ref" >&2
    exit 1
  fi
  CLONE="$WORK/clone"
  git clone -q "$BARE_REMOTE" "$CLONE"
  if git -C "$CLONE" log --all -S"$FLAG" --format='%H' -- \
      internal/launch-rehearsal-notes.md | grep -q .; then
    echo "setup error: a fresh clone can see the ghost flag" >&2
    exit 1
  fi
  CLONE_COUNT="$(git -C "$CLONE" rev-list --count HEAD)"
  [[ "$CLONE_COUNT" == "100" ]] || {
    echo "setup error: clone sees $CLONE_COUNT commits, want 100" >&2; exit 1
  }
  echo "LOCAL-ONLY OK: ghost object retained but unreachable after force-push"
  echo "ghost URL would be: https://github.com/${GH_USER}/${GH_REPO}/commit/${GHOST_SHA}"
  exit 0
fi

# The live sequence is intentionally old-main -> clean-main. This makes the
# force-push event's payload.before equal to the flag-bearing commit.
git remote add origin "$REMOTE_URL"
publish_history

echo "DONE."
echo "ghost URL: https://github.com/${GH_USER}/${GH_REPO}/commit/${GHOST_SHA}"
echo "events:    https://api.github.com/users/${GH_USER}/events/public"
echo "verify the live object and event before launching the challenge."

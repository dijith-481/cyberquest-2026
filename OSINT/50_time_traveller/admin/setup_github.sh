#!/usr/bin/env bash
# Time Traveller — GitHub mirror setup.
#
# Builds a clean Book Haven repository, publishes a flag-bearing commit as
# main, and then force-pushes a clean replacement. The flag-bearing commit is
# left unreachable from refs, while GitHub's activity event exposes its SHA.
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
#   FLAG=<flag>                 override the 2026 flag (update the docs too)
#   SITE_SOURCE=<path>          use a different copy of deployment/index.html
set -euo pipefail

CHALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GH_USER="${GH_USER:-oe-mira-doodle-0417}"
GH_REPO="${GH_REPO:-book-haven}"
FLAG="${FLAG:-cyber_quest{t1m3_tr4v3ll3r_r3v1v3d_9e4c7a}}"
SITE_SOURCE="${SITE_SOURCE:-$CHALL_DIR/deployment/index.html}"
REMOTE_URL="${REMOTE_URL:-git@github.com:${GH_USER}/${GH_REPO}.git}"
LOCAL_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --local-only) LOCAL_ONLY=1 ;;
    *) echo "usage: $0 [--local-only]" >&2; exit 2 ;;
  esac
done

[[ -f "$SITE_SOURCE" ]] || { echo "site source not found: $SITE_SOURCE" >&2; exit 1; }
[[ "$GH_USER" =~ ^[A-Za-z0-9-]+$ ]] || { echo "invalid GH_USER" >&2; exit 1; }
[[ "$GH_REPO" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "invalid GH_REPO" >&2; exit 1; }
[[ -n "$FLAG" ]] || { echo "FLAG must not be empty" >&2; exit 1; }
if [[ "$FLAG" == *$'\n'* ]]; then
  echo "FLAG must be a single line" >&2
  exit 1
fi

mkdir -p /tmp/opencode
WORK="$(mktemp -d /tmp/opencode/time-traveller-setup.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
REPO="$WORK/$GH_REPO"
mkdir -p "$REPO"
cd "$REPO"

git init -q -b main
git config user.name "book-haven mirror"
git config user.email "mirror@localhost"
git config commit.gpgsign false
git config core.autocrlf false

commit() {
  local message="$1"
  local date="$2"
  GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" git add -A
  GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" git commit -qm "$message"
}

# A maintained-looking, clean repository.
cat > README.md <<'EOF'
# Book Haven

The clean catalog mirror for the Book Haven Book Shop.
The public page is intentionally ordinary; the interesting record is in its
Git history.
EOF
commit "catalog: initialize Book Haven mirror" "2026-08-03T10:00:00Z"

cp "$SITE_SOURCE" index.html
commit "site: publish Book Haven catalog" "2026-08-10T10:00:00Z"

cat > CHANGELOG.md <<'EOF'
# Changelog

- 2026-08-10 — initial catalog publication
EOF
commit "catalog: add first changelog entry" "2026-08-17T10:00:00Z"

cat > notes.md <<'EOF'
Catalog notes
=============

The shop is static. There is no checkout backend and no customer database.
EOF
commit "notes: document static catalog" "2026-08-24T10:00:00Z"

echo "rev 3: responsive catalog polish" >> CHANGELOG.md
commit "site: responsive catalog polish" "2026-08-31T10:00:00Z"

echo "rev 4: updated newsletter copy" >> CHANGELOG.md
commit "site: update newsletter copy" "2026-09-07T10:00:00Z"

# The common ancestor of both tips. The ghost branch is published first.
BASE_SHA="$(git rev-parse HEAD)"

git switch -q -c ghost
mkdir -p archive
cat > archive/catalog-export-20250724.txt <<EOF
Book Haven catalog export
=========================
The export predates the clean catalog. Preserve the original import record.

$FLAG
EOF
commit "archive: preserve the original catalog export" "2026-09-10T18:02:00Z"
GHOST_SHA="$(git rev-parse HEAD)"

# Build the clean replacement from the common ancestor, not from the ghost.
git switch -q main
echo "rev 5: confirm clean catalog state" >> CHANGELOG.md
commit "cleanup: remove archived export from main" "2026-09-10T18:03:00Z"
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

# Keep the object alive while the branch is being replaced, then publish the
# old tip as main. The next push is the force-push players must discover.
publish_history() {
  git push -q origin "$GHOST_SHA:refs/heads/ghost-tmp"
  git push -q --force origin "$GHOST_SHA:refs/heads/main"
  git push -q --force origin "$CLEAN_SHA:refs/heads/main"
  git push -q --delete origin ghost-tmp
}

echo "GHOST_SHA=$GHOST_SHA"
echo "CLEAN_SHA=$CLEAN_SHA"
echo "force-push: $GHOST_SHA -> $CLEAN_SHA"

if [[ "$LOCAL_ONLY" == 1 ]]; then
  BARE_REMOTE="$WORK/remote.git"
  git init -q --bare "$BARE_REMOTE"
  git remote add origin "$BARE_REMOTE"
  publish_history
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
      archive/catalog-export-20250724.txt | grep -q .; then
    echo "setup error: a fresh clone can see the ghost flag" >&2
    exit 1
  fi
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

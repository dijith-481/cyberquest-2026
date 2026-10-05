# Early Access — solution

**Flag:** `cyber_quest{3v3ry_y0u_0n3_f33d_a4f2c1}`

The flag is planted in a commit that is published as `main`, then replaced by
a clean commit using a force push. The rewritten commit is no longer reachable
from a normal clone, but GitHub can expose its SHA through the public activity
feed and can continue serving the commit object directly for a while.

## Walkthrough

1. **Open the handout and read its metadata.** The rendered page is an ordinary
   coming-soon site for orbit, ordinary engineering's multiverse social
   platform: hero, waitlist, features (all TBA), roadmap, FAQ. Nothing on the
   visible page mentions a flag, and that is the point.

   The only live signal is in the page metadata. Among the generic tags sits:

   ```html
   <meta name="author" content="aetheria-loml">
   ```

   Easiest to find with **View Page Source** and searching for `meta`, or
   `curl` on the page and grepping for `author`.

2. **Inspect the contributor's mirror.** Open
   `https://github.com/aetheria-loml/orbit`. Its current `main`
   branch contains the same clean waitlist site and no flag. Do not stop at
   the repository's normal commit list: the interesting commit was removed
   from that history by a force push.

   The visible history (about a hundred commits of ordinary site construction)
does contain one lure, buried around position 40 so the first commits page
never shows it: a commit titled
   `remove accidentally leaked staging key`. Its diff touches only the
   changelog — the key itself is nowhere in any reachable object, because the
   clean branch was built from the pre-leak ancestor rather than from the
   leak. That message is the confirmation you are in the right repository.

3. **Find the force-push event.** Open the repository's activity page:

   ```text
   https://github.com/aetheria-loml/orbit/activity
   ```

   One row reads `aetheria-loml force pushed to main`, with a hash range
   like `849ab81...34ae1ec`. That range is `before...head`: the old `main`
   tip (the ghost commit containing the flag) and the clean rewritten tip.
   Click the range to open the compare view — the compare URL carries both
   full SHAs, so copy the `before` SHA from there.

   The same event is also visible through the API when GitHub exposes it
   (brand-new accounts sometimes lag here; the activity page above is the
   reliable route):

   ```sh
   curl -s 'https://api.github.com/users/aetheria-loml/events/public?per_page=100&page=1'
   ```

   If the account is busy, check the next pages as well. In the matching event,
   read `payload.before`. That is the old `main` tip —
   the ghost commit containing the flag. `payload.head` is the clean rewritten
   tip. The equivalent compare URL is:

   ```text
   https://github.com/aetheria-loml/orbit/compare/<BEFORE>...<HEAD>
   ```

4. **Open the dangling commit directly.** While GitHub still retains the
   object, visit:

   ```text
   https://github.com/aetheria-loml/orbit/commit/<BEFORE>
   ```

   Do not stop at the compare view: it diffs from the merge-base, so a file
   that exists only on the ghost side never appears there. You need the
   commit object itself — it lists one added file,

   The commit adds `internal/launch-rehearsal-notes.md`. Its contents are:

   ```text
   STAGING_WAITLIST_KEY="cyber_quest{3v3ry_y0u_0n3_f33d_a4f2c1}"
   ```

   The same SHA can be inspected from a clone when GitHub accepts the fetch:

   ```sh
   git fetch origin <BEFORE>
   git show <BEFORE>:internal/launch-rehearsal-notes.md
   ```

## Organizer setup and checks

The mirror is built and published with:

```sh
GH_USER=aetheria-loml GH_REPO=orbit \
  bash admin/setup_github.sh
```

Create an empty public mirror repository first. The default account/repository
in the script are placeholders; set `GH_USER` and `GH_REPO` to the real mirror
(and update the author meta in `deployment/index.html` if it differs).
The setup script intentionally replaces that repository's generated `main`
history, so do not point it at a repository whose history must be preserved.

The script builds ~100 commits (39 build + lure at 40 + 60 polish), publishes
the flag-bearing tip as `main` first, then force-pushes the clean replacement
and removes the temporary ref. Use `--local-only` to rehearse the exact
sequence without credentials:

```sh
bash admin/setup_github.sh --local-only
bash admin/verify.sh
```

For a live smoke test, provide the SHA printed by the setup script:

```sh
GHOST_SHA=<printed-sha> GH_USER=aetheria-loml GH_REPO=orbit \
  bash admin/verify.sh --live
```

GitHub does not promise that an unreachable object will remain available for
exactly one month. Retention depends on repository activity and GitHub's
object cleanup, and the public events API is also limited by event count and
age. Publish and verify the mirror before the event, and keep the handout live
only for the intended window. The placeholder account must also stay quiet:
every unrelated push to the account risks paging the force-push event out of
the API.

## Why the decoys are traps

- The launch-archive link (`web.archive.org/.../orbit/`) shows only the
  pre-launch teaser. It is useful for recognizing the site, but the flag was
  never in any archived page — it exists only in the force-pushed mirror commit.
- `robots.txt`, `/beta/`, `humans.txt`, `security.txt`, the footer source
  link, and the staging TODO in `assets/app.js` all describe retired or
  TBA surfaces. They waste time convincingly and contain no flag.

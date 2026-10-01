# Time Traveller — solution

**Flag:** `cyber_quest{t1m3_tr4v3ll3r_r3v1v3d_9e4c7a}`

This is a tribute to the 2025 **Time Traveller** challenge by Aaron Kurian
(published in `1337kid/CyberQuest-2025` at commit
`be5698ab12b7383797ab5a196641b0f8ba1184e1`). The original challenge was a Book
Haven page whose old HTML comment was recoverable through the Wayback Machine.
The 2026 version keeps the same visible shop, but the current flag is not in
the deployed HTML.

The flag is planted in a commit that is published as `main`, then replaced by
a clean commit using a force push. The rewritten commit is no longer reachable
from a normal clone, but GitHub can expose its SHA through the public activity
feed and can continue serving the commit object directly for a while.

## Walkthrough

1. **Open the handout and view its source.** The rendered page is the ordinary
   2025 Book Haven page: a book catalog with *The Time Traveler's Library*,
   *1984*, and *Pride and Prejudice*. At the bottom of the HTML is a harmless
   looking source comment:

   ```html
   <!-- mirror: github.com/oe-mira-doodle-0417/book-haven -->
   ```

   The comment is not rendered, so it is easiest to find with **View Page
   Source**, the browser inspector, or `curl` on the page.

2. **Inspect the mirror.** Open
   `https://github.com/oe-mira-doodle-0417/book-haven`. Its current `main`
   branch contains the same clean Book Haven page and no flag. Do not stop at
   the repository's normal commit list: the interesting commit was removed
   from that history by a force push.

3. **Find the force-push event.** The account's public activity contains a
   `PushEvent` for `book-haven`. The API form is useful when the UI hides an
   older event:

   ```sh
   curl -s 'https://api.github.com/users/oe-mira-doodle-0417/events/public?per_page=100&page=1'
   ```

   If the account is busy, check the next pages as well. In the matching event,
   read `payload.before`. That is the old `main` tip —
   the ghost commit containing the flag. `payload.head` is the clean rewritten
   tip. The equivalent compare URL is:

   ```text
   https://github.com/oe-mira-doodle-0417/book-haven/compare/<BEFORE>...<HEAD>
   ```

4. **Open the dangling commit directly.** While GitHub still retains the
   object, visit:

   ```text
   https://github.com/oe-mira-doodle-0417/book-haven/commit/<BEFORE>
   ```

   The commit adds `archive/catalog-export-20250724.txt`. Its contents are:

   ```text
   cyber_quest{t1m3_tr4v3ll3r_r3v1v3d_9e4c7a}
   ```

   The same SHA can be inspected from a clone when GitHub accepts the fetch:

   ```sh
   git fetch origin <BEFORE>
   git show <BEFORE>:archive/catalog-export-20250724.txt
   ```

## Organizer setup and checks

The mirror is built and published with:

```sh
GH_USER=oe-mira-doodle-0417 GH_REPO=book-haven \
  bash admin/setup_github.sh
```

Create an empty public mirror repository first. The default account/repository
in the script are placeholders; set `GH_USER` and `GH_REPO` to the real mirror
(and update the source breadcrumb in `deployment/index.html` if it differs).
The setup script intentionally replaces that repository's generated `main`
history, so do not point it at a repository whose history must be preserved.

The script first publishes the flag-bearing commit, then force-pushes a clean
main and removes the temporary ref. Use `--local-only` to rehearse the exact
sequence without credentials:

```sh
bash admin/setup_github.sh --local-only
bash admin/verify.sh
```

For a live smoke test, provide the SHA printed by the setup script:

```sh
GHOST_SHA=<printed-sha> GH_USER=oe-mira-doodle-0417 GH_REPO=book-haven \
  bash admin/verify.sh --live
```

GitHub does not promise that an unreachable object will remain available for
exactly one month. Retention depends on repository activity and GitHub's
object cleanup, and the public events API is also limited by event count and
age. Publish and verify the mirror before the event, and keep the handout live
only for the intended window.

## Why the 2025 route is a trap

The original snapshot used for the visual comparison is:

```text
https://web.archive.org/web/20250724161844id_/https://time-traveler-one.vercel.app/
```

The Wayback Machine still contains the 2025 page and its old flag. It is a
useful way to recognize the website, but it cannot solve this edition: the
2026 flag is generated only in the force-pushed mirror commit. Players who
find the archived page should follow the source breadcrumb to the mirror and
look at its history instead.

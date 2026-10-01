# Book Haven deployment

This directory is the static handout for **Time Traveller**. Serve the contents
of this directory as the challenge site; no backend is required.

The page is intentionally the same visible Book Haven shop as the 2025
challenge. Its source contains the non-rendered mirror breadcrumb used by the
current edition. Do not add the flag to this directory: the organizer creates
the flag-bearing commit in the separate GitHub mirror and then rewrites
`main`.

For a quick local preview:

```sh
python3 -m http.server 8050 --directory deployment
```

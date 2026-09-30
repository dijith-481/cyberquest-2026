The Lost Year — fonts and third-party material

The deployment sets the entire site in **IBM Plex Mono**, self-hosted from
`assets/fonts/`:

- IBM Plex Mono — SIL Open Font License 1.1
  https://fonts.google.com/specimen/IBM+Plex+Mono

No font file is fetched from a CDN at request time; the `@font-face` rules in
`assets/fonts.css` point at the `.woff2` files committed alongside them, and
the stack falls back to the platform monospace if they fail to load.

`UnifrakturMaguntia` (also SIL OFL 1.1,
https://fonts.google.com/specimen/UnifrakturMaguntia) is **no longer used**.
The site previously set its display type in blackletter over a parchment
palette with a sword cursor, which put it in a medieval register that the
prose no longer matched. The `.woff2` remains on disk so the licence record
stays accurate, but nothing references it and no `@font-face` rule for it
remains.

No other third-party material is used. All text, layout and inline SVG
artwork (the favicon) were written for this challenge.

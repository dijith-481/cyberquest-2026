# Payroll Photo — solution

## The shape

`all_hands.jpg` is a 320x240 baseline JPEG carrying two `APP1` segments
before the frame header and nothing hidden in the pixels at all. Exactly
**one** flag-shaped string is in the file, and it is not where any viewer
will show it to you.

## Step 1 — what a viewer shows you

Open the file. Every image viewer on earth displays the EXIF
`ImageDescription` right under the photo, because that is what the field
is for:

```
ImageDescription     Annual all-hands, College Ground. Badge photo, do not circulate.
Software             FacilitiesPhone 2.1 (build 0918)
DateTime             2026:09:18 09:14:11
DateTimeOriginal     2026:09:18 09:14:11
PixelXDimension      320
PixelYDimension      240
```

That is an ordinary caption and an ordinary camera string. `exiftool`,
`identify -verbose`, `exiv2`, Windows Explorer properties, macOS Preview —
all of them show you this and nothing else of consequence. It is a dead
end, and it is dead *quietly*: there is no joke flag to submit, no
rejection to puzzle over. You have simply read the half of the metadata
that is meant to be read.

## Step 2 — the field nobody renders

The same file carries a second `APP1`: an **XMP** packet. XMP is the
modern Adobe/XMP metadata format, and the field that matters is Dublin
Core `dc:description`:

```xml
<rdf:Description ...
    xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:description><rdf:Alt><rdf:li xml:lang="x-default">cyber_quest{th3_m3t4d4t4_1s_n0t_th3_phot0}
  </rdf:li></rdf:Alt></dc:description>
</rdf:Description>
```

That is the flag. It is 804 bytes of XMP sitting in the file, and it is
in no rendered panel, because image viewers implement EXIF and
essentially nobody implements XMP on the description field.

## The shortest solve

```
exiftool -dc:description all_hands.jpg
```

`exiftool` prints EXIF *and* XMP side by side, so a player who runs it
sees the ordinary caption and the flag in one listing and has to notice
that only one of them is in a metadata system their photo app actually
reads. That is the intended experience: one tool, two blocks, one
answer.

## Alternate solves

```
strings -a all_hands.jpg | grep cyber_quest        # 1 hit, and it is in the XMP
exifprint all_hands.jpg                            # EXIF only; will not find it
python3 admin/solve.py all_hands.jpg               # stdlib, walks APP1 itself
```

The reference solver is stdlib-only on purpose: it parses the JPEG
segment table, decodes the EXIF IFD by hand, then reads the XMP packet,
which proves the flag is reachable from the raw bytes on a machine with
nothing installed.

## Difficulty notes

100 points, easy. The only tools needed are free, and the one real step is
realising the answer is not where the viewer is looking. It is a
*correlation* solve, not a lookup: the player must notice that EXIF and
XMP are two different metadata systems in one file, that the popular one
shows them nothing interesting, and that the less popular one is not
shown by the thing they are already using.

`verify.sh` asserts the EXIF `ImageDescription` is still present — it is
the visible half of the lesson, not bait — that the flag is not in EXIF,
and that the flag does not survive stripping every `APPn` segment, so it
can never quietly become a stego challenge.

### On the decoy that used to be here

This challenge previously carried a second flag-shaped string in EXIF's
`ImageDescription`, so that checking the obvious place produced a
plausible-looking rejection. It was removed, and the removal is asserted
in `verify.sh` rather than merely noted here.

The reason is a shortcut it created rather than the joke itself. Every
real flag in this event ends in a random hex suffix; the decoy did not. So
a player could scan the file for anything matching `cyber_quest{...}`,
notice which candidate carried a hex suffix, and submit that — without
reading a single metadata field, and without ever learning the thing the
challenge is about. A decoy that lets you skip the actual lesson is
worse than no decoy.

With one flag in the file there is no shape-based way to pick it, and the
EXIF block goes back to being what it should have been: a real, readable,
boring caption that a viewer renders and that tells you nothing.

## What verification establishes

The handout regenerates byte-identically. **ImageMagick, an independent
implementation, parses and fully decodes the JPEG** — `identify` reports
`JPEG 320x240 8-bit` and a full pixel decode yields mean luminance 0.436,
i.e. a real image, not a blank or saturated frame. That check exists
because the JPEG was written by a vendored encoder in `deployment/jpeg.py`
rather than by an imaging library, so it needs a second opinion. The
stdlib solver then recovers the expected flag from a fresh copy, the
answer line is asserted equal to the expected flag, the file is confirmed
to contain exactly **one** flag-shaped string (so a decoy cannot be
reintroduced silently), the EXIF description is confirmed still present,
and the flag is confirmed absent once the `APPn` metadata is stripped.

### A note for whoever regenerates this
`deployment/jpeg.py` is a vendored baseline encoder. If you swap it for
Pillow or `ffmpeg`, re-run `verify.sh` and check the SHA-256 changes
*and* that the two metadata segments still sit before `SOF0` — a
different encoder will produce different entropy data, so the recorded
hash will not match.

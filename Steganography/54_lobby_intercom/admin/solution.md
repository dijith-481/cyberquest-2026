# Lobby Intercom — solution

## The shape

`lobby_intercom.wav` is 7.08 s of mono 16-bit PCM at 44100 Hz. There is
**no LSB steganography in this file at all** — that is the whole point of
sitting next to 39 B-Side. The message is a picture in the
**frequency domain**.

## Step 1 — do not reach for steghide

Everything a player tries first fails, by design:

- `steghide` does not handle WAV at all
- `binwalk` finds no embedded object
- a naive LSB dump is garbage — `verify.sh` asserts this for bit planes
  1, 2, 4 and 8, and for the raw sample bytes

The file is a legitimate 44-byte-header PCM WAV with no `LIST`/`INFO`/
`id3` chunk, so there is no metadata to read either.

## Step 2 — look at it

Open it in Audacity and switch the track view to **Spectrogram**. Or:

```
ffmpeg -i lobby_intercom.wav -lavfi showspectrumpic=s=1400x500 spec.png
sox lobby_intercom.wav -n spectrogram -o spec.png
```

The flag is legible as text, drawn in the 1800–4200 Hz band:

```
cyber_quest{th3_sp3ctr0gr4m_1s_l0ud}
```

The low broadband hum that makes the file sound like a room rather than a
test tone sits at 180 Hz and its harmonics, well below the message band,
so it never occludes the picture.

## How it is encoded

A 5x7 pixel-font rendering of the flag is mapped onto the spectrogram
plane. Each ink cell is a ~28 ms sine burst placed at a specific
(time, frequency) coordinate:

- time axis: one pixel column = 30 ms, six columns per character
- frequency axis: seven rows spanning 1800–4200 Hz, ~400 Hz apart
- every burst is windowed with a raised cosine so it does not click

Nothing about this requires the player to know the encoding. They see
text. That is the payoff — the "aha" is that a WAV can be a canvas, and
it is worth 200 points precisely because the first three things everyone
tries all fail.

## Alternate solves

```
ffmpeg -i lobby_intercom.wav -lavfi showspectrumpic=s=2000x800:legend=1 out.png
python3 admin/solve.py lobby_intercom.wav     # stdlib, no numpy, no scipy
```

The reference solver does **not** compute a full STFT. It probes only the
grid coordinates with the Goertzel algorithm (a single-frequency DFT),
takes the median magnitude across the whole grid as the noise floor, and
thresholds at 35% of the way to the peak. That is faster and far less
ambiguous than picking bins out of an FFT, and it means the solve runs on
a stock Python with nothing installed.

## Difficulty notes

200 points, easy. The tools are free and ubiquitous (Audacity ships on
most desktops, ffmpeg and sox are one package away), and the skill being
taught is simply "look at the spectrogram" — the same instinct as 25
Gridlock, where the answer is visible once you open the file the right
way.

## What verification establishes

The handout regenerates byte-identically and the shipped file matches the
generator (no drift). It is a real RIFF/WAVE, PCM mono 16-bit @ 44100 Hz,
with **no `LIST`/`INFO`/`id3 `/`bext`/`cue `/`cart` chunk** — so there is
no metadata side channel. The message is confirmed absent from the raw
sample bytes and from bit planes 1, 2, 4 and 8. **ffprobe and a full
ffmpeg decode** confirm the file is valid audio with no reported errors.
The stdlib solver then decodes the expected flag from a fresh copy, the
answer is asserted equal to the expected string, and the decoder is
required to produce no unmatched glyphs (`?`).

### A note for whoever regenerates this
`admin/solve.py` imports the geometry constants from
`deployment/generate.py`. If you change `F_LO`, `F_HI`, `COL_MS`,
`GLYPH_W/H` or `ADVANCE`, re-run `verify.sh` — the solver will follow the
generator, and the drift check will catch a mismatched committed WAV.
Changing the flag means adding any new characters to `FONT`; the
generator fails loudly on an unmapped glyph rather than rendering a blank
cell.

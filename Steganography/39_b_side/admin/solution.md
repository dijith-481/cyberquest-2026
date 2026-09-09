# 39_b_side — solution

**Flag:** `cyber_quest{cr0ss_0v3r_t0_th3_b_s1d3_7f3a}`
**Difficulty:** medium

## The setup

The handout is `support_hold.wav`: six seconds of the support line's hold
music, archived for QA. Stereo, 16-bit PCM, exactly as the recorder wrote
it. The two channels were recorded from different feeds, and they behave
differently: the left plays a chord pad, the right hums a steady tone.

## Step 1 — inspect the file, split the channels

```bash
file support_hold.wav
# RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, stereo 44100 Hz
python3 -c "import wave; w = wave.open('support_hold.wav'); \
  print(w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes())"
# 2 2 44100 264600
```

Plot or FFT each channel separately. The left is musical (a slow A/F/G/A
pad with hiss); the right is a near-pure 440 Hz tone. The archived shift
transcript is the hint, in retrospect: "Please stay on the line. We will
pick things up whenever the other side crosses over." The *other side*
(the right channel) *crosses over* (zero). Pick things up there.

## Step 2 — confirm plain LSB extraction is garbage

```bash
python3 -c "
import wave, struct
w = wave.open('support_hold.wav','rb')
s = struct.unpack('<%dh' % (w.getnframes()*2), w.readframes(w.getnframes()))
bits = ''.join(str(x & 1) for x in s[0::2])
print(bytes(int(bits[i:i+8],2) for i in range(0, 512, 8))[:64])"
# b"5!\xeb/..." — noise. The LSB of every sample is a dead end, by design.
```

## Step 3 — read left LSBs at right-channel rising zero crossings

Carrier rule, straight from the signal — no offsets, no seeds:

```
for n >= 1: if right[n-1] < 0 and right[n] >= 0: bit = LSB(left[n])
```

```bash
python3 admin/solve.py handout/support_hold.wav
# cyber_quest{cr0ss_0v3r_t0_th3_b_s1d3_7f3a}
```

## Step 4 — framed bitstream confirms the decode

Bits are MSB first. The stream is framed, not naked ASCII:

```
43 51            magic "CQ"
00 2A            u16-BE payload length (42)
<42 payload>     the full flag, ASCII
<4 crc32>        u32-BE zlib CRC32 of the payload
```

The solver checks the magic, slices exactly `length` bytes, and verifies
the CRC before printing. 2639 crossings exist; the first 400 carry the
packet and the rest are decoys, which is why the length header matters.

## Step 5 — submit

`cyber_quest{cr0ss_0v3r_t0_th3_b_s1d3_7f3a}`. Done.

#!/usr/bin/env python3
"""39_b_side — generate handout/support_hold.wav.

Stereo 16-bit PCM hold-music stego (stdlib only, deterministic, seed 39).

Encoding:
  RIGHT channel = selector, LEFT channel = data.
  A carrier is any index n >= 1 with a rising zero crossing on the right:
      right[n-1] < 0 and right[n] >= 0
  LSB(left[n]) at each carrier = next secret bit, MSB first.
  All other left LSBs are randomized so a naive full-stream LSB dump
  is garbage.

Bitstream framing (gives solvers confirmation + makes the build testable):
  magic   2 bytes  "CQ" (0x43 0x51)
  length  u16 BE   len(payload)
  payload bytes    the full flag, ASCII
  crc32   u32 BE   zlib CRC32 of payload

The first len(bits) crossings carry the framed payload; any remaining
crossings keep their random decoy LSBs (the length header tells the
solver where the message ends).

Right channel is a clean 440 Hz tone (one rising crossing per period);
left channel is a four-chord synth pad with tape hiss. The channels
behave differently on purpose: that is the tell.
"""
import math
import os
import random
import struct
import wave
import zlib

SEED = 39
SR = 44100
DUR_S = 6.0
N = int(SR * DUR_S)

FLAG = "cyber_quest{cr0ss_0v3r_t0_th3_b_s1d3_7f3a}"

TONE_HZ = 440.0
TONE_AMP = 12000.0

# Four-chord hold-music pad (A / F / G / A), one chord per quarter.
CHORDS = [
    [220.00, 277.18, 329.63],
    [174.61, 220.00, 261.63],
    [196.00, 246.94, 293.66],
    [220.00, 277.18, 329.63],
]
NOTE_AMP = 2800.0
FADE_S = 0.05


def frame_payload(flag: str) -> bytes:
    payload = flag.encode("ascii")
    assert len(payload) < 0x10000
    return b"CQ" + struct.pack(">H", len(payload)) + payload + struct.pack(
        ">I", zlib.crc32(payload) & 0xFFFFFFFF
    )


def main() -> None:
    rng = random.Random(SEED)
    packet = frame_payload(FLAG)
    bits = [(b >> (7 - i)) & 1 for b in packet for i in range(8)]
    print(f"flag: {FLAG}")
    print(f"packet: {len(packet)} bytes -> {len(bits)} bits")

    # ---- right channel: clean pilot tone (the selector) ----
    right = [
        int(round(TONE_AMP * math.sin(2.0 * math.pi * TONE_HZ * n / SR)))
        for n in range(N)
    ]
    crossings = [n for n in range(1, N) if right[n - 1] < 0 <= right[n]]
    print(f"rising zero crossings (right): {len(crossings)}")
    assert len(crossings) >= len(bits) + 16, "not enough carriers"

    # ---- left channel: chord pad + hiss, LSBs pre-randomized ----
    seg = N // 4
    fade = int(SR * FADE_S)
    left = []
    for n in range(N):
        ci = min(n // seg, 3)
        chord = CHORDS[ci]
        pos = n - ci * seg
        seg_len = N - ci * seg if ci == 3 else seg
        # raised-cosine edge fades so chords join without clicks
        env = 1.0
        if pos < fade:
            env = 0.5 - 0.5 * math.cos(math.pi * pos / fade)
        elif pos > seg_len - fade:
            env = 0.5 - 0.5 * math.cos(math.pi * (seg_len - pos) / fade)
        v = sum(
            NOTE_AMP * math.sin(2.0 * math.pi * f * n / SR) for f in chord
        )
        v = v * env + rng.uniform(-25.0, 25.0)
        s = int(round(v))
        s = max(-32768, min(32767, s))
        s = (s & ~1) | rng.getrandbits(1)  # randomize LSB: naive dump = noise
        left.append(s)

    # ---- embed: first len(bits) crossings carry the packet ----
    for n, bit in zip(crossings, bits):
        left[n] = (left[n] & ~1) | bit

    out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "handout",
        "support_hold.wav",
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)
    frames = bytearray()
    for n in range(N):
        frames += struct.pack("<hh", left[n], right[n])
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(bytes(frames))
    print(f"wrote {out} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    main()

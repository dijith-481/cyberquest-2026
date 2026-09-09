#!/usr/bin/env python3
"""39_b_side — reference solver (stdlib only).

1. Read the stereo 16-bit PCM WAV, split L/R channels.
2. Find rising zero crossings on the RIGHT channel:
       right[n-1] < 0 and right[n] >= 0
3. Collect LSB(left[n]) at those positions, MSB first.
4. Parse the CQ framing: magic "CQ", u16-BE length, payload, u32-BE CRC32.
5. Verify the CRC and print the flag.
"""
import struct
import sys
import wave
import zlib


def read_wav(path):
    with wave.open(path, "rb") as w:
        assert w.getnchannels() == 2, "want stereo"
        assert w.getsampwidth() == 2, "want 16-bit PCM"
        n = w.getnframes()
        raw = w.readframes(n)
    total = n * 2
    samples = struct.unpack("<%dh" % total, raw)
    left = samples[0::2]
    right = samples[1::2]
    return left, right, w.getframerate()


def main(path):
    left, right, sr = read_wav(path)
    print(f"samples: {len(left)}, rate: {sr}", file=sys.stderr)

    crossings = [n for n in range(1, len(right)) if right[n - 1] < 0 <= right[n]]
    print(f"rising zero crossings (right): {len(crossings)}", file=sys.stderr)

    bits = [(left[n] & 1) for n in crossings]
    assert len(bits) >= 48, "bitstream too short for a header"
    data = bytes(
        int("".join(map(str, bits[k:k + 8])), 2)
        for k in range(0, len(bits) - len(bits) % 8, 8)
    )
    assert data[:2] == b"CQ", f"bad magic: {data[:2]!r}"
    (length,) = struct.unpack(">H", data[2:4])
    payload = data[4:4 + length]
    assert len(payload) == length, "bitstream truncated"
    (want,) = struct.unpack(">I", data[4 + length:8 + length])
    got = zlib.crc32(payload) & 0xFFFFFFFF
    assert got == want, f"CRC mismatch: got {got:08x} want {want:08x}"
    flag = payload.decode("ascii")
    print(f"crc ok ({got:08x}), payload {length} bytes", file=sys.stderr)
    print(flag)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "support_hold.wav")

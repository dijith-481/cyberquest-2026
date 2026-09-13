#!/usr/bin/env python3
"""Recover the straight gallery and visible flag from the player PNG alone.

No builder imports, expected flag, original texture, crop coordinates, or
font are needed. Constants below are from the public CindyJS demo source.
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image


def recover(rgb, size=2048, aspect=1196/1360):
    beta = 1 - 1j*aspect
    c = 2*np.pi*aspect
    offset_difference = complex(.701-.151, .531-.901)
    result = np.empty((size, size, 3), np.uint8)
    for first in range(0, size, 64):
        y, x = np.mgrid[first:min(first+64, size), :size]
        w = (-6+(x+.5)*12/size) + 1j*(6-(y+.5)*12/size)
        base = np.log(w) + c*offset_difference
        chosen = np.zeros(w.shape, complex)
        radius = np.zeros(w.shape)
        for branch in range(-3, 4):
            z = np.exp((base + 2j*np.pi*branch)/beta)
            good = (abs(z.real) <= 6) & (abs(z.imag) <= 6)
            good &= abs(z) > radius
            chosen[good], radius[good] = z[good], abs(z[good])
        if np.any(radius == 0):
            raise ValueError("uncovered inverse coordinates")
        # Nearest-neighbour sampling keeps the blue LSB intact.
        sx = np.clip(np.floor((chosen.real+6)*rgb.shape[1]/12).astype(int), 0, rgb.shape[1]-1)
        sy = np.clip(np.floor((6-chosen.imag)*rgb.shape[0]/12).astype(int), 0, rgb.shape[0]-1)
        result[first:first+len(w)] = rgb[sy, sx]
    return result


def save_results(rgb, directory):
    straight = recover(rgb)
    directory.mkdir(parents=True, exist_ok=True)
    Image.fromarray(straight).save(directory / "straightened.png")
    Image.fromarray((rgb[:, :, 2] & 1)*255).save(directory / "curled-blue-lsb.png")
    plane = Image.fromarray((straight[:, :, 2] & 1)*255)
    plane.save(directory / "flag.png")
    # Discover the text's bounds from its ink, not organizer coordinates.
    bounds = plane.getbbox()
    if bounds:
        left, top, right, bottom = bounds
        plane.crop((max(left-24, 0), max(top-24, 0),
                    min(right+24, plane.width), min(bottom+24, plane.height))).save(directory / "flag-crop.png")
    return straight


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path, default=Path("recovered"))
    args = parser.parse_args()
    with Image.open(args.image) as image:
        if image.mode != "RGB" or image.width != image.height:
            raise ValueError("expected the square, lossless RGB handout")
        save_results(np.array(image), args.output)
    print(f"Open {args.output / 'straightened.png'} for the gallery.")
    print(f"Open {args.output / 'flag.png'} and read the text left to right, joining the two lines.")

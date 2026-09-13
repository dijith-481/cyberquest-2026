"""The public CindyJS Droste mapping with its actual texture and offsets.

ffSpiral(z) = (re + im*i*aspect)*log(z)/(2*pi*aspect) - aa.
The artwork viewport is [-8,4] x [-6,6], relative to SpiralCenter=(-2,0).
Both axes relative to that centre therefore span [-6,6].
"""
import numpy as np

ASPECT = 1196 / 1360
C = 2 * np.pi * ASPECT
BETA = 1 - 1j * ASPECT
STRAIGHT_OFFSET = .151 + .901j  # off + offtab_6_5, geometry (1,0)
CURLED_OFFSET = .701 + .531j    # off + offtab_6_4, geometry (1,-1)


def pixel_plane(size, first=0, count=None):
    stop = size if count is None else min(first + count, size)
    y, x = np.mgrid[first:stop, :size]
    return (-6 + (x + .5) * 12 / size) + 1j * (6 - (y + .5) * 12 / size)


def texture_sample(texture, z, curled):
    """Bilinear sampling of the same repeated log texture as the website."""
    uv = ((BETA if curled else 1) * np.log(z) / C
          - (CURLED_OFFSET if curled else STRAIGHT_OFFSET))
    h, w = texture.shape[:2]
    sx = (uv.real % 1) * w - .5
    sy = (1 - (uv.imag * ASPECT) % 1) * h - .5
    ix, iy = np.floor(sx).astype(int), np.floor(sy).astype(int)
    dx, dy = (sx - ix)[..., None], (sy - iy)[..., None]
    return ((1-dy) * ((1-dx)*texture[iy % h, ix % w] + dx*texture[iy % h, (ix+1) % w])
            + dy * ((1-dx)*texture[(iy+1) % h, ix % w] + dx*texture[(iy+1) % h, (ix+1) % w]))


def straight_from_curled(z):
    return np.exp(BETA * np.log(z) + C * (STRAIGHT_OFFSET - CURLED_OFFSET))


def repeat_in_view(z):
    """Select the largest scale-duplicate fitting in the straight square."""
    winding = np.ceil(np.log(np.maximum(abs(z.real), abs(z.imag)) / 6) / C)
    return z / np.exp(C * winding)


def sample_mask(mask, z):
    z = repeat_in_view(z)
    h, w = mask.shape
    x = np.clip(np.floor((z.real + 6) * w / 12).astype(int), 0, w-1)
    y = np.clip(np.floor((6 - z.imag) * h / 12).astype(int), 0, h-1)
    return mask[y, x]

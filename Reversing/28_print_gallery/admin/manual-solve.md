# Manual solve — organizer only

Run these stages in one terminal. They use only the PNG extracted from the
player ZIP; no generator, organizer solver, source texture, or expected flag
is imported. All intermediate files go into a new temporary directory.

## 1. Extract the image

```bash
CHALLENGE=/home/dijith/.Data/Dev/excel/2026/ctf/Reversing/28_print_gallery
WORK=$(mktemp -d /tmp/print-gallery-manual.XXXXXX)
python3 -m venv "$WORK/venv"
source "$WORK/venv/bin/activate"
python -m pip install numpy==2.3.5 Pillow==12.3.0
unzip "$CHALLENGE/28_print_gallery.zip" -d "$WORK"
cd "$WORK"
file print-gallery.png
```

The archive contains one 4096×4096 RGB PNG. Identify the artwork as the
CindyJS Print Gallery example and research the straight `(1,0)` and curled
`(1,-1)` settings. The event handout itself contains no links or notes.

## 2. Inspect the blue low bit

```bash
python - <<'PY'
import numpy as np
from PIL import Image
image = Image.open('print-gallery.png')
print(image.mode, image.size, image.info)
rgb = np.array(image)
Image.fromarray((rgb[:, :, 2] & 1)*255).save('01-curled-blue-lsb.png')
PY
```

Open `01-curled-blue-lsb.png`. It reveals bent writing. The next step
straightens the full gallery; the hidden text follows the same mapping.

## 3. Apply the public inverse mapping

From the demo source and its 1196×1360 artwork:

```text
a = 1196/1360
C = 2*pi*a
beta = 1 - i*a
straight offset = 0.151 + 0.901i
curled offset   = 0.701 + 0.531i
```

Equating the two views' texture coordinates gives:

```text
z_curled = exp((Log(z_straight) + C*(curled_offset-straight_offset)
                + 2*pi*i*k)/beta)
```

The image square spans `[-6,6]` around the spiral centre. Enumerate the
logarithm's branches and keep the largest visible copy. These are public
example parameters, not a secret crop or key.

```bash
python - <<'PY'
import numpy as np
from PIL import Image

rgb = np.array(Image.open('print-gallery.png').convert('RGB'))
n = 2048
a = 1196/1360
beta = 1 - 1j*a
c = 2*np.pi*a
offset = complex(.701-.151, .531-.901)
straight = np.empty((n, n, 3), np.uint8)

for start in range(0, n, 64):
    y, x = np.mgrid[start:min(start+64, n), :n]
    w = (-6+(x+.5)*12/n) + 1j*(6-(y+.5)*12/n)
    chosen = np.zeros(w.shape, complex)
    radius = np.zeros(w.shape)
    for k in range(-3, 4):
        z = np.exp((np.log(w)+c*offset+2j*np.pi*k)/beta)
        good = (abs(z.real)<=6) & (abs(z.imag)<=6)
        good &= abs(z)>radius
        chosen[good] = z[good]
        radius[good] = abs(z[good])
    assert np.all(radius > 0)
    sx = np.clip(np.floor((chosen.real+6)*rgb.shape[1]/12).astype(int), 0, rgb.shape[1]-1)
    sy = np.clip(np.floor((6-chosen.imag)*rgb.shape[0]/12).astype(int), 0, rgb.shape[0]-1)
    straight[start:start+len(w)] = rgb[sy, sx]

Image.fromarray(straight).save('02-straightened.png')
Image.fromarray((straight[:, :, 2] & 1)*255).save('03-flag.png')
print('Created 02-straightened.png and 03-flag.png')
PY
```

Open `02-straightened.png`. The gallery should now show the clean window
view approved for the challenge. Nearest-neighbour sampling preserves the
low bit; applying bilinear interpolation directly to RGB would damage it.

## 4. Read the flag

Open `03-flag.png`. Read the ordinary text left to right, joining its two
lines without whitespace. No binary grid, OCR, or ASCII conversion is needed.

Optional commands on a Linux desktop:

```bash
xdg-open 02-straightened.png
xdg-open 03-flag.png
```

The resulting flag is:

```text
cyber_quest{l0g_unw1nds_th3_g4ll3ry_7a3c9e}
```

## Where the parameters come from

The source's `ffSpiral` function uses the image's aspect ratio. Its `offtab`
contains the two view offsets, including `corr` and the initial `off`.
The visible artwork spans `[-8,4]×[-6,6]`, and `SpiralCenter=(-2,0)` makes
that `[-6,6]×[-6,6]` in centred coordinates. Changing geometry from `(1,-1)`
to `(1,0)` produces the straight view. The supplied source code documents
all of these values.

- https://cindyjs.org/gallery/main/Droste/
- https://github.com/CindyJS/website/blob/master/src/gallery/main/Droste/droste.html
- https://www.youtube.com/watch?v=ldxFjLJ3rVY
- https://pub.math.leidenuniv.nl/~smitbde/escherdroste/page_menu=symmetry.html

The video and research explain the transform; the actual demo asset's
aspect ratio supplies its precise calibration. These explanations remain
organizer-only. The player ZIP stays PNG-only.

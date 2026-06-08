#!/usr/bin/env python3
"""Bake a transparent-background PNG master of the estate pentacle mark.

The source is bright cyan/magenta linework on Void Purple (#1a0f2e). We key alpha
to luminance: void -> transparent, glowing lines -> opaque, with a soft ramp so the
ion-glow halos fade naturally. Result blends onto any background (esp. void) with no
square edge. Closes the _estate README TODO (transparent master).

Outputs:
  - themes/arcaeon/assets/images/pentacle-mark.png   (for Hugo to process)
  - <business-brand>/_estate/pentacle/pentacle-mark.png  (canonical master)
"""
from PIL import Image
from pathlib import Path

SRC = Path.home() / "mnemosyne/business-brand/_estate/pentacle/estate-mark-pentacle.jpg"
THEME_OUT = Path(__file__).resolve().parent.parent / "themes/arcaeon/assets/images/pentacle-mark.png"
ESTATE_OUT = SRC.with_name("pentacle-mark.png")

# luminance ramp (0..1): below LO -> fully transparent, above HI -> fully opaque
LO, HI = 0.11, 0.34

def smoothstep(lo, hi, x):
    if x <= lo: return 0.0
    if x >= hi: return 1.0
    t = (x - lo) / (hi - lo)
    return t * t * (3 - 2 * t)

img = Image.open(SRC).convert("RGB")
px = img.load()
w, h = img.size
out = Image.new("RGBA", (w, h))
opx = out.load()

for y in range(h):
    for x in range(w):
        r, g, b = px[x, y]
        luma = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
        a = smoothstep(LO, HI, luma)
        opx[x, y] = (r, g, b, int(round(a * 255)))

# crop to non-transparent bounding box, keep square
bbox = out.getbbox()
if bbox:
    out = out.crop(bbox)
# pad back to square so it centers cleanly
s = max(out.size)
sq = Image.new("RGBA", (s, s), (0, 0, 0, 0))
sq.paste(out, ((s - out.width) // 2, (s - out.height) // 2))
out = sq

THEME_OUT.parent.mkdir(parents=True, exist_ok=True)
out.save(THEME_OUT)
out.save(ESTATE_OUT)
print(f"wrote {THEME_OUT}  ({out.width}x{out.height})")
print(f"wrote {ESTATE_OUT}")

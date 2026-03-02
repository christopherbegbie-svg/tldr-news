"""
Generates a TLDR profile picture (1000x1000) for X and Instagram.
Run: python make_profile_pic.py
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

SIZE = 1000
OUT = Path("tldr_profile.png")

BG_DARK   = (13, 17, 23)       # #0D1117
BLUE      = (88, 166, 255)     # #58A6FF
WHITE     = (255, 255, 255)    # pure white for maximum contrast
MID_GREY  = (48, 54, 61)

img = Image.new("RGB", (SIZE, SIZE), BG_DARK)
draw = ImageDraw.Draw(img, "RGBA")

# ── Rim glow — draw outlined rings so the centre stays dark ──────────────────
cx, cy = SIZE // 2, SIZE // 2
rim_start = int(SIZE / 2 * 0.72)   # start of glow (72% of radius outward)
for r in range(SIZE // 2, rim_start, -3):
    rel = (r - rim_start) / (SIZE / 2 - rim_start)   # 1.0 at edge, 0 at rim_start
    alpha = int(60 * rel)
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        outline=(88, 166, 255, alpha),
        width=3,
    )

# ── Outer ring ────────────────────────────────────────────────────────────────
ring_w = 18
draw.ellipse([ring_w, ring_w, SIZE - ring_w, SIZE - ring_w],
             outline=BLUE, width=ring_w)

# ── Inner accent ring ─────────────────────────────────────────────────────────
draw.ellipse([ring_w + 22, ring_w + 22, SIZE - ring_w - 22, SIZE - ring_w - 22],
             outline=MID_GREY, width=2)

# ── "TLDR" wordmark ───────────────────────────────────────────────────────────
ASSETS = Path(__file__).parent / "assets" / "fonts"

def load(name, size):
    for p in (list(ASSETS.glob(f"*{name}*")) if ASSETS.exists() else []):
        try:
            return ImageFont.truetype(str(p), size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

font_main = load("Bold", 220)
font_sub  = load("Regular", 52)

# Main wordmark — centred
text = "TLDR"
bbox = draw.textbbox((0, 0), text, font=font_main)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
tx = (SIZE - tw) // 2 - bbox[0]
ty = (SIZE - th) // 2 - bbox[1] - 40

draw.text((tx, ty), text, font=font_main, fill=WHITE)

# Blue underline bar
bar_y = ty + th + 20
bar_x0 = tx + 20
bar_x1 = tx + tw - 20
draw.rectangle([bar_x0, bar_y, bar_x1, bar_y + 8], fill=BLUE)

# Tagline
tag = "Global News Digest"
tbbox = draw.textbbox((0, 0), tag, font=font_sub)
tw2 = tbbox[2] - tbbox[0]
draw.text(
    ((SIZE - tw2) // 2 - tbbox[0], bar_y + 32),
    tag,
    font=font_sub,
    fill=(190, 200, 210),
)

img.save(OUT, "PNG")
print(f"Saved: {OUT.resolve()}")

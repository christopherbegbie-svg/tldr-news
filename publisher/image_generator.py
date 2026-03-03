"""
Generates 1080x1080 news card images for Instagram posts using Pillow.
No external fonts required — falls back to Pillow's built-in font gracefully,
but looks much better with a downloaded font (see assets/fonts/).
"""

from __future__ import annotations

import logging
import tempfile
import textwrap
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from news.models import Article
from summarizer.claude_client import SummaryResult

logger = logging.getLogger(__name__)

# ── Layout constants ───────────────────────────────────────────────────────────
WIDTH = 1080
HEIGHT = 1080

BG_COLOR = (13, 17, 23)           # #0D1117  — GitHub dark
ACCENT_COLOR = (88, 166, 255)     # #58A6FF  — bright blue
TEXT_PRIMARY = (230, 237, 243)    # near-white
TEXT_SECONDARY = (139, 148, 158)  # muted grey
CHIP_BG = (30, 215, 96, 220)      # Spotify green with alpha
CHIP_TEXT = (0, 0, 0)

PADDING = 72
LOGO_Y = 64

CATEGORY_CHIP_Y = 160
HEADLINE_Y = 240
SUBHEADLINE_Y = 560
DIVIDER_Y = 680
SOURCE_Y = 720
BRAND_Y = 960

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

# ── Font loading ───────────────────────────────────────────────────────────────

def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = list(ASSETS_DIR.glob(f"*{name}*")) if ASSETS_DIR.exists() else []
    for path in candidates:
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            pass
    # Fall back to default (looks plain but always works)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# ── Drawing helpers ────────────────────────────────────────────────────────────

def _draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: tuple,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ── Main card generator ────────────────────────────────────────────────────────

def create_card(article: Article, summary: SummaryResult) -> Path:
    """
    Draw a 1080x1080 news card and save it to a temp file.
    Returns the path to the PNG file.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img, "RGBA")

    # Subtle gradient overlay (lighter at top)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(HEIGHT):
        alpha = int(40 * (1 - y / HEIGHT))
        od.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, alpha))
    img.paste(overlay, (0, 0), overlay)
    draw = ImageDraw.Draw(img)

    # ── Fonts ──────────────────────────────────────────────────────────────
    font_logo   = _load_font("Bold", 52)
    font_chip   = _load_font("Bold", 26)
    font_h1     = _load_font("Bold", 46)
    font_sub    = _load_font("Regular", 34)
    font_source = _load_font("Regular", 28)
    font_brand  = _load_font("Bold", 30)

    # ── TLDR Wordmark ──────────────────────────────────────────────────────
    draw.text((PADDING, LOGO_Y), "TLDR", font=font_logo, fill=ACCENT_COLOR)

    # ── Category chip ──────────────────────────────────────────────────────
    chip_text = article.category.upper()
    chip_bbox = draw.textbbox((0, 0), chip_text, font=font_chip)
    chip_w = chip_bbox[2] - chip_bbox[0] + 32
    chip_h = chip_bbox[3] - chip_bbox[1] + 16
    _draw_rounded_rect(
        draw,
        (PADDING, CATEGORY_CHIP_Y, PADDING + chip_w, CATEGORY_CHIP_Y + chip_h),
        radius=8,
        fill=ACCENT_COLOR,
    )
    draw.text(
        (PADDING + 16, CATEGORY_CHIP_Y + 8),
        chip_text,
        font=font_chip,
        fill=(13, 17, 23),
    )

    # ── Accent bar ─────────────────────────────────────────────────────────
    bar_y = CATEGORY_CHIP_Y + chip_h + 24
    draw.rectangle([(PADDING, bar_y), (PADDING + 6, bar_y + 220)], fill=ACCENT_COLOR)

    # ── Headline ───────────────────────────────────────────────────────────
    headline = summary.get("card_headline", article.title)[:80]
    max_text_width = WIDTH - PADDING * 2 - 80  # account for accent bar + gap + font metric slack
    lines = _wrap_text(headline, font_h1, max_text_width, draw)[:4]
    h_x = PADDING + 22
    h_y = bar_y + 8
    for line in lines:
        draw.text((h_x, h_y), line, font=font_h1, fill=TEXT_PRIMARY)
        bbox = draw.textbbox((h_x, h_y), line, font=font_h1)
        h_y += (bbox[3] - bbox[1]) + 12

    # ── Sub-headline ───────────────────────────────────────────────────────
    sub = summary.get("card_subheadline", "")[:100]
    if sub:
        sub_lines = _wrap_text(sub, font_sub, WIDTH - PADDING * 2, draw)[:3]
        s_y = max(h_y + 32, SUBHEADLINE_Y)
        for line in sub_lines:
            draw.text((PADDING, s_y), line, font=font_sub, fill=TEXT_SECONDARY)
            bbox = draw.textbbox((PADDING, s_y), line, font=font_sub)
            s_y += (bbox[3] - bbox[1]) + 8

    # ── Divider ────────────────────────────────────────────────────────────
    draw.rectangle(
        [(PADDING, DIVIDER_Y), (WIDTH - PADDING, DIVIDER_Y + 1)],
        fill=(48, 54, 61),
    )

    # ── Source ─────────────────────────────────────────────────────────────
    draw.text(
        (PADDING, SOURCE_Y),
        f"via {article.source}",
        font=font_source,
        fill=TEXT_SECONDARY,
    )

    # ── Brand footer ───────────────────────────────────────────────────────
    draw.text(
        (PADDING, BRAND_Y),
        "TLDR: Your daily global news digest",
        font=font_brand,
        fill=ACCENT_COLOR,
    )
    draw.text(
        (WIDTH - PADDING - 120, BRAND_Y),
        "@tldr_news",
        font=font_brand,
        fill=TEXT_SECONDARY,
    )

    # ── Save ───────────────────────────────────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(
        suffix=".png", delete=False, prefix="tldr_card_"
    )
    img.save(tmp.name, "PNG", optimize=True)
    logger.info("News card saved: %s", tmp.name)
    return Path(tmp.name)

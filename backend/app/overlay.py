"""Generates the overlay for a card, based on its suit and value.

The overlay is a transparent PNG (same aspect ratio as the print card) drawn
with Pillow: a thick white frame border, plus the rank/suit badges (in the
suit's color) in the corners -- no color wash over the artwork. It is the
single source of truth for the "card look", used both for the live preview
in the browser (served as a cached PNG, stacked over the photo with CSS)
and for the composited export (uploaded photo + overlay merged for the zip
download, see routers/export.py which also handles the photo's 50% opacity
blend onto white, resized to fit *inside* the border, before this overlay
is composited on top).

The border is drawn as a plain (square-cornered) rectangle on purpose: the
browser rounds the displayed corners via CSS (`border-radius` on the shared
container both the photo and this overlay sit in), so there is exactly one
source of corner-rounding and the two layers can never mismatch. A raster
with its own rounded corners baked in previously caused a sliver of photo
to leak past the (differently-rounded) CSS clip at the corners. Square
corners are also simply correct for the print file, which is meant to be
cut to an exact rectangle (70 x 121mm).

Algorithm (deterministic function of suit + value):
  - White rectangular frame border around the whole card.
  - Corner badges (top-left, and bottom-right rotated 180°) showing the
    rank/value and the suit symbol, colored with the suit's own color.
  - Jokers: same treatment, but the corner badge spells out "JOKER" as
    stacked letters (one per line, top to bottom) instead of a rank, with
    a color cycling per joker so the 6 are visually distinguishable.
"""
from __future__ import annotations

import colorsys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import deck

# Exact print size: 2.75in x 4.75in (~70 x 121mm) at 300dpi.
PRINT_DPI = 300
PRINT_SIZE_PX = (825, 1425)
CARD_RATIO = PRINT_SIZE_PX[0] / PRINT_SIZE_PX[1]  # width / height

# Default size for the live-preview overlay served to the browser: same
# 11:19 ratio as the print size, smaller for fast loading.
PREVIEW_SIZE_PX = (550, 950)

# Border thickness as a fraction of the card width, applied uniformly (in
# raw pixels) to all 4 sides. The frontend CSS hardcodes the same ratio
# (see CardTile.vue / style.css) to inset the photo to fit inside it --
# keep both in sync if this changes.
BORDER_RATIO = 0.13

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
]


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in _FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _hls_to_rgb(h: float, l: float, s: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)


def border_width_px(width: int) -> int:
    """The border's pixel thickness for a card rendered at this width --
    shared by render_overlay() and the export compositor so the photo's
    inset always lines up exactly with where the border is drawn."""
    return max(6, int(width * BORDER_RATIO))


# Red, gold, green, cyan, blue, magenta -- cycled so the 6 jokers are each
# visually distinguishable from one another.
JOKER_HUES = [0.0, 0.13, 0.33, 0.5, 0.66, 0.83]


def card_style(suit_code: str | None, value: str, joker_index: int | None = None) -> dict:
    """Deterministic style for a given card: the corner badge's text
    line(s) and color -- no wash, no court-card embellishments. The
    value's own text already conveys the rank; the color conveys the
    suit."""
    if value == deck.JOKER_VALUE:
        hue = JOKER_HUES[((joker_index or 1) - 1) % len(JOKER_HUES)]
        return {
            "is_joker": True,
            "lines": list("JOKER"),  # stacked, one letter per line
            "color": _hls_to_rgb(hue, 0.46, 0.85),
        }

    suit = deck.SUITS_BY_CODE[suit_code]
    return {
        "is_joker": False,
        "lines": [value, suit.symbol],  # rank, then suit symbol below it
        "color": _hex_to_rgb(suit.color),
    }


def _draw_corner_badge(draw: ImageDraw.ImageDraw, xy: tuple[int, int], lines: list[tuple[str, ImageFont.FreeTypeFont]], color: tuple[int, int, int], halo_radius: int) -> None:
    x, y = xy
    halo = (255, 255, 255, 235)
    ty = y
    for text, font in lines:
        # Characters have different left side-bearings in the font (e.g.
        # "J" sits further from the pen origin than "O"/"K"/"E"/"R"), so
        # drawing every line at the same raw x misaligns the visible ink.
        # Measure each line's actual ink box and shift so *that* -- not
        # the font's pen origin -- lines up at x.
        ink_left = draw.textbbox((x, ty), text, font=font, stroke_width=halo_radius)[0]
        tx = x + (x - ink_left)
        # Pillow's native stroke draws a clean, efficient outline behind
        # the glyph so the colored text stays legible over any photo.
        draw.text((tx, ty), text, font=font, fill=color + (255,), stroke_width=halo_radius, stroke_fill=halo)
        ty += font.size + 2


def render_overlay(suit_code: str | None, value: str, joker_index: int | None = None, size: tuple[int, int] = PREVIEW_SIZE_PX) -> Image.Image:
    """Render the RGBA overlay PNG for a card at the given pixel size."""
    width, height = size
    style = card_style(suit_code, value, joker_index)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    border_width = border_width_px(width)

    # Thick white frame border, square corners (see module docstring for
    # why) -- the whole "overlayed color" wash is gone; only this border
    # and the corner badges remain.
    draw.rectangle(
        [(0, 0), (width - 1, height - 1)],
        outline=(255, 255, 255, 255),
        width=border_width,
    )

    # Corner badges (rank/symbol, or "JOKER" spelled vertically), top-left
    # and bottom-right (rotated), inset to sit inside the white frame.
    margin = border_width + int(width * 0.02)
    halo_radius = max(2, int(width * 0.014))  # 2x the original fixed radius

    if style["is_joker"]:
        letter_font = _find_font(int(width * 0.095))
        lines = [(ch, letter_font) for ch in style["lines"]]
    else:
        label_font = _find_font(int(width * 0.13))
        symbol_font = _find_font(int(width * 0.10))
        value_text, symbol_text = style["lines"]
        lines = [(value_text, label_font), (symbol_text, symbol_font)]

    _draw_corner_badge(draw, (margin, margin), lines, style["color"], halo_radius)

    badge_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    badge_draw = ImageDraw.Draw(badge_layer)
    _draw_corner_badge(badge_draw, (margin, margin), lines, style["color"], halo_radius)
    badge_layer = badge_layer.rotate(180)
    img = Image.alpha_composite(img, badge_layer)

    return img


@lru_cache(maxsize=256)
def _cached_overlay_bytes(suit_code: str | None, value: str, joker_index: int | None, width: int, height: int) -> bytes:
    import io

    overlay = render_overlay(suit_code, value, joker_index, size=(width, height))
    buf = io.BytesIO()
    overlay.save(buf, format="PNG")
    return buf.getvalue()


def get_overlay_png_bytes(suit_code: str | None, value: str, joker_index: int | None = None, size: tuple[int, int] = PREVIEW_SIZE_PX) -> bytes:
    return _cached_overlay_bytes(suit_code, value, joker_index, size[0], size[1])

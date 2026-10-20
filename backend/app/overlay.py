"""Generates the overlay for a card, based on its suit and value.

The overlay is a transparent PNG (same aspect ratio as the print card) drawn
with Pillow: a thick white frame border, plus the rank/suit badges (in the
suit's color) in the corners -- no color wash over the artwork. It is the
single source of truth for the "card look", used both for the live preview
in the browser (served as a cached PNG, stacked over the photo with CSS)
and for the composited export (uploaded photo + overlay merged for the zip
download, see routers/export.py which also handles the photo's 50% opacity
blend onto white before this overlay is composited on top).

Algorithm (deterministic function of suit + value):
  - White rounded-rect frame border around the whole card.
  - Corner badges (top-left, and bottom-right rotated 180°) showing the
    rank/value and the suit symbol, colored with the suit's own color.
  - Jokers: same treatment, with "J1".."J6" as the rank label (so they
    stay readable instead of looking like a stray "Star" number) and a
    color cycling per joker so the 6 are visually distinguishable.
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


# Red, gold, green, cyan, blue, magenta -- cycled so the 6 jokers are each
# visually distinguishable from one another (and from the gold "Star" suit).
JOKER_HUES = [0.0, 0.13, 0.33, 0.5, 0.66, 0.83]


def card_style(suit_code: str | None, value: str, joker_index: int | None = None) -> dict:
    """Deterministic style for a given card: just a label/symbol/color --
    no wash, no court-card embellishments. The value's own text already
    conveys the rank; the color conveys the suit."""
    if value == deck.JOKER_VALUE:
        hue = JOKER_HUES[((joker_index or 1) - 1) % len(JOKER_HUES)]
        return {
            "label": f"J{joker_index or 1}",
            "symbol": "★",
            "color": _hls_to_rgb(hue, 0.46, 0.85),
        }

    suit = deck.SUITS_BY_CODE[suit_code]
    return {
        "label": value,
        "symbol": suit.symbol,
        "color": _hex_to_rgb(suit.color),
    }


def _draw_corner_badge(draw: ImageDraw.ImageDraw, xy: tuple[int, int], label: str, symbol: str, color: tuple[int, int, int], font_label, font_symbol) -> None:
    x, y = xy
    # White halo behind the colored text so it stays legible over any photo.
    halo = (255, 255, 255, 235)
    for text, font, ty in ((label, font_label, y), (symbol, font_symbol, y + font_label.size + 2)):
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if dx or dy:
                    draw.text((x + dx, ty + dy), text, font=font, fill=halo)
        draw.text((x, ty), text, font=font, fill=color + (255,))


def render_overlay(suit_code: str | None, value: str, joker_index: int | None = None, size: tuple[int, int] = PREVIEW_SIZE_PX) -> Image.Image:
    """Render the RGBA overlay PNG for a card at the given pixel size."""
    width, height = size
    style = card_style(suit_code, value, joker_index)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    radius = int(width * 0.045)
    border_width = max(4, int(width * 0.065))

    # Thick white frame border -- the whole "overlayed color" wash is gone;
    # only this border and the corner badges remain.
    draw.rounded_rectangle(
        [(border_width // 2, border_width // 2), (width - 1 - border_width // 2, height - 1 - border_width // 2)],
        radius=radius,
        outline=(255, 255, 255, 255),
        width=border_width,
    )

    # Corner badges (rank/symbol), top-left and bottom-right (rotated),
    # inset enough to sit inside the white frame rather than under it.
    label_size = int(width * 0.13)
    symbol_size = int(width * 0.10)
    font_label = _find_font(label_size)
    font_symbol = _find_font(symbol_size)
    margin = border_width + int(width * 0.02)

    _draw_corner_badge(draw, (margin, margin), style["label"], style["symbol"], style["color"], font_label, font_symbol)

    badge_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    badge_draw = ImageDraw.Draw(badge_layer)
    _draw_corner_badge(badge_draw, (margin, margin), style["label"], style["symbol"], style["color"], font_label, font_symbol)
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

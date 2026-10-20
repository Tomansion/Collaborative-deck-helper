"""Generates the colored overlay for a card, based on its suit and value.

The overlay is a transparent PNG (same aspect ratio as a poker card) drawn
with Pillow: a tinted wash + a frame border in the suit's color, plus the
rank/suit badges in the corners. It is the single source of truth for the
"card look", used both for the live preview in the browser (served as a
cached PNG) and for the composited export (uploaded photo + overlay merged
for the zip download).

Algorithm (deterministic function of suit + value):
  - Each suit has a base hue (see deck.py).
  - Number cards (3..10) get a light, increasingly saturated wash as the
    rank grows, with a thin border.
  - Court cards (V, D, R) get a stronger, more opaque wash, a thicker
    border and an inner gold accent line -- they are meant to look more
    "royal" than number cards, like real face cards.
  - Jokers get a festive multicolor (rainbow) border that cycles through
    hue depending on which of the 6 jokers it is, so they are visually
    distinguishable, plus a diagonal "JOKER" ribbon.
"""
from __future__ import annotations

import colorsys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import deck

CARD_RATIO = 1000 / 1400  # width / height, standard poker card proportions

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


def _rgb_to_hls(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = (c / 255 for c in rgb)
    return colorsys.rgb_to_hls(r, g, b)


JOKER_HUES = [0.0, 0.14, 0.33, 0.5, 0.66, 0.83]  # red, gold, green, cyan, blue, magenta


def card_style(suit_code: str | None, value: str, joker_index: int | None = None) -> dict:
    """Deterministic style parameters for a given card.

    Returns a dict describing the wash color/opacity, border color/width
    and whether this is a "court" (face) card, used by both the preview
    overlay renderer and (indirectly) the export compositor.
    """
    if value == deck.JOKER_VALUE:
        hue = JOKER_HUES[((joker_index or 1) - 1) % len(JOKER_HUES)]
        wash = _hls_to_rgb(hue, 0.55, 0.85)
        border = _hls_to_rgb(hue, 0.45, 0.9)
        return {
            "is_joker": True,
            "is_court": False,
            "wash_rgb": wash,
            "wash_alpha": 70,
            "border_rgb": border,
            "border_width_ratio": 0.030,
            "accent_rgb": _hex_to_rgb("#E0A800"),
            "label": str(joker_index or 1),
            "symbol": "★",
        }

    suit = deck.SUITS_BY_CODE[suit_code]
    hue, base_l, base_s = _rgb_to_hls(_hex_to_rgb(suit.color))
    rank = deck.value_rank(value)  # 0 (value 3) .. 10 (value R)
    is_court = value in deck.COURT_VALUES

    if is_court:
        court_rank = {"V": 0, "D": 1, "R": 2}[value]
        wash_alpha = 115 + court_rank * 20  # V=115, D=135, R=155
        lightness = max(0.30, base_l - 0.05 * court_rank)
        border_width_ratio = 0.028 + 0.006 * court_rank
    else:
        wash_alpha = 45 + int(rank / 7 * 55)  # ~45 (value 3) .. ~100 (value 10)
        lightness = min(0.82, base_l + 0.30 - rank * 0.012)
        border_width_ratio = 0.012

    wash = _hls_to_rgb(hue, lightness, min(1.0, base_s + 0.1))
    border = _hls_to_rgb(hue, max(0.25, base_l - 0.1), min(1.0, base_s + 0.15))

    return {
        "is_joker": False,
        "is_court": is_court,
        "wash_rgb": wash,
        "wash_alpha": wash_alpha,
        "border_rgb": border,
        "border_width_ratio": border_width_ratio,
        "accent_rgb": _hex_to_rgb("#D4AF37"),  # gold accent for court cards
        "label": value,
        "symbol": suit.symbol,
    }


def _draw_corner_badge(draw: ImageDraw.ImageDraw, xy, label: str, symbol: str, color, font_label, font_symbol, flip: bool, canvas_size):
    x, y = xy
    text = label
    # outline for legibility over any photo
    outline = (255, 255, 255, 235)
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font_label, fill=outline)
    draw.text((x, y), text, font=font_label, fill=color + (255,))

    sym_y = y + font_label.size + 2
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            if dx or dy:
                draw.text((x + dx, sym_y + dy), symbol, font=font_symbol, fill=outline)
    draw.text((x, sym_y), symbol, font=font_symbol, fill=color + (255,))


def render_overlay(suit_code: str | None, value: str, joker_index: int | None = None, size: tuple[int, int] = (500, 700)) -> Image.Image:
    """Render the RGBA overlay PNG for a card at the given pixel size."""
    width, height = size
    style = card_style(suit_code, value, joker_index)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    radius = int(width * 0.045)
    border_width = max(3, int(width * style["border_width_ratio"]))

    # Soft color wash across the whole card so the underlying photo still
    # shows through, stronger towards the edges for a vignette feel.
    wash_rgb = style["wash_rgb"]
    wash_alpha = style["wash_alpha"]
    wash_layer = Image.new("RGBA", (width, height), wash_rgb + (0,))
    wash_draw = ImageDraw.Draw(wash_layer)
    wash_draw.rounded_rectangle(
        [(0, 0), (width - 1, height - 1)], radius=radius, fill=wash_rgb + (wash_alpha,)
    )
    img = Image.alpha_composite(img, wash_layer)
    draw = ImageDraw.Draw(img)

    # Frame border.
    border_rgb = style["border_rgb"]
    draw.rounded_rectangle(
        [(border_width // 2, border_width // 2), (width - 1 - border_width // 2, height - 1 - border_width // 2)],
        radius=radius,
        outline=border_rgb + (255,),
        width=border_width,
    )

    # Inner gold accent line for court cards & jokers.
    if style["is_court"] or style["is_joker"]:
        inset = border_width + max(4, int(width * 0.012))
        draw.rounded_rectangle(
            [(inset, inset), (width - 1 - inset, height - 1 - inset)],
            radius=max(2, radius - inset // 2),
            outline=style["accent_rgb"] + (210,),
            width=max(2, int(width * 0.006)),
        )

    # Corner badges (rank/symbol), top-left and bottom-right (rotated).
    label_size = int(width * 0.11)
    symbol_size = int(width * 0.09)
    font_label = _find_font(label_size)
    font_symbol = _find_font(symbol_size)
    margin = int(width * 0.06)

    badge_color = tuple(min(255, c) for c in border_rgb)
    _draw_corner_badge(draw, (margin, margin), style["label"], style["symbol"], badge_color, font_label, font_symbol, False, (width, height))

    badge_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    badge_draw = ImageDraw.Draw(badge_layer)
    _draw_corner_badge(badge_draw, (margin, margin), style["label"], style["symbol"], badge_color, font_label, font_symbol, False, (width, height))
    badge_layer = badge_layer.rotate(180)
    img = Image.alpha_composite(img, badge_layer)

    if style["is_joker"]:
        draw = ImageDraw.Draw(img)
        ribbon_font = _find_font(int(width * 0.085))
        ribbon = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ribbon_draw = ImageDraw.Draw(ribbon)
        text = "JOKER"
        bbox = ribbon_draw.textbbox((0, 0), text, font=ribbon_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        ribbon_draw.text(((width - tw) / 2, (height - th) / 2), text, font=ribbon_font, fill=style["accent_rgb"] + (235,))
        ribbon = ribbon.rotate(-25, resample=Image.BICUBIC, center=(width / 2, height / 2))
        img = Image.alpha_composite(img, ribbon)

    return img


@lru_cache(maxsize=256)
def _cached_overlay_bytes(suit_code: str | None, value: str, joker_index: int | None, width: int, height: int) -> bytes:
    import io

    overlay = render_overlay(suit_code, value, joker_index, size=(width, height))
    buf = io.BytesIO()
    overlay.save(buf, format="PNG")
    return buf.getvalue()


def get_overlay_png_bytes(suit_code: str | None, value: str, joker_index: int | None = None, size: tuple[int, int] = (500, 700)) -> bytes:
    return _cached_overlay_bytes(suit_code, value, joker_index, size[0], size[1])

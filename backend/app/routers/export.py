from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from PIL import Image as PILImage
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import config, deck, overlay
from ..database import get_db
from ..models import Card

router = APIRouter(prefix="/api", tags=["export"])

# Exact print size: 2.75in x 4.75in (~70 x 121mm) at 300dpi -- see overlay.py.
EXPORT_SIZE = overlay.PRINT_SIZE_PX
PLACEHOLDER_RGB = (255, 255, 255)  # matches the overlay's white frame


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "carte"


def _cover_resize(img: PILImage.Image, size: tuple[int, int]) -> PILImage.Image:
    target_w, target_h = size
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = round(src_w * scale), round(src_h * scale)
    img = img.resize((new_w, new_h), PILImage.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _fade_onto_white(photo_rgb: PILImage.Image, opacity: float = 0.5) -> PILImage.Image:
    """Blend a photo at the given opacity onto a solid white background,
    so it reads as "faded" rather than tinted by a color wash."""
    white = PILImage.new("RGB", photo_rgb.size, (255, 255, 255))
    return PILImage.blend(white, photo_rgb, opacity)


def build_card_image(card: Card, size: tuple[int, int] = EXPORT_SIZE) -> PILImage.Image | None:
    """Composite the card's chosen photo (faded to 50% opacity onto white)
    with its overlay. Returns None if the card has no chosen photo (caller
    decides whether to skip it or fall back to a placeholder background)."""
    current = card.current_image
    base: PILImage.Image
    if current is not None:
        photo_path = config.UPLOADS_DIR / current.filename
        if not photo_path.exists():
            return None
        with PILImage.open(photo_path) as src:
            photo = _cover_resize(src.convert("RGB"), size)
        base = _fade_onto_white(photo).convert("RGBA")
    else:
        return None

    overlay_img = overlay.render_overlay(card.suit, card.value, card.joker_index, size=size)
    composited = PILImage.alpha_composite(base, overlay_img)
    return composited.convert("RGB")


def build_placeholder_image(card: Card, size: tuple[int, int] = EXPORT_SIZE) -> PILImage.Image:
    base = PILImage.new("RGBA", size, PLACEHOLDER_RGB + (255,))
    overlay_img = overlay.render_overlay(card.suit, card.value, card.joker_index, size=size)
    composited = PILImage.alpha_composite(base, overlay_img)
    return composited.convert("RGB")


@router.get("/export/zip")
def export_zip(include_missing: bool = False, db: Session = Depends(get_db)) -> StreamingResponse:
    cards = db.scalars(select(Card).order_by(Card.order_index)).all()

    buffer = io.BytesIO()
    included, skipped = 0, 0
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for index, card in enumerate(cards, start=1):
            image = build_card_image(card)
            if image is None:
                if not include_missing:
                    skipped += 1
                    continue
                image = build_placeholder_image(card)

            suit_part = card.suit or f"joker-{card.joker_index}"
            filename = f"{index:02d}_{_slugify(suit_part)}_{_slugify(card.value)}.jpg"
            img_buf = io.BytesIO()
            image.save(img_buf, format="JPEG", quality=92, dpi=(overlay.PRINT_DPI, overlay.PRINT_DPI))
            zf.writestr(filename, img_buf.getvalue())
            included += 1

    buffer.seek(0)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    headers = {
        "Content-Disposition": f'attachment; filename="les-cinq-rois-{timestamp}.zip"',
        "X-Export-Included": str(included),
        "X-Export-Skipped": str(skipped),
    }
    return StreamingResponse(buffer, media_type="application/zip", headers=headers)

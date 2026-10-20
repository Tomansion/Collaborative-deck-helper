from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import config, deck, overlay, schemas
from ..database import get_db
from ..models import Card, HistoryEntry, Image
from ..ws_manager import manager

router = APIRouter(prefix="/api", tags=["cards"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
EXT_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _image_url(image: Image) -> str:
    return f"/uploads/{image.filename}"


def _overlay_url(card: Card) -> str:
    return f"/api/cards/{card.id}/overlay.png"


def _to_card_out(card: Card) -> schemas.CardOut:
    current = card.current_image
    return schemas.CardOut(
        id=card.id,
        suit=card.suit,
        value=card.value,
        joker_index=card.joker_index,
        order_index=card.order_index,
        label=card.label,
        description=card.description,
        overlay_url=_overlay_url(card),
        current_image=(
            schemas.ImageOut(
                id=current.id,
                url=_image_url(current),
                original_filename=current.original_filename,
                uploaded_at=current.uploaded_at,
                is_current=current.is_current,
            )
            if current
            else None
        ),
        image_count=len(card.images),
    )


def _to_card_detail(card: Card) -> schemas.CardDetailOut:
    base = _to_card_out(card).model_dump()
    images = [
        schemas.ImageOut(
            id=img.id,
            url=_image_url(img),
            original_filename=img.original_filename,
            uploaded_at=img.uploaded_at,
            is_current=img.is_current,
        )
        for img in sorted(card.images, key=lambda i: i.uploaded_at, reverse=True)
    ]
    return schemas.CardDetailOut(**base, images=images)


def _get_card_or_404(db: Session, card_id: int) -> Card:
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Carte introuvable")
    return card


def _log_history(db: Session, card: Card, change_type: str, summary: str) -> HistoryEntry:
    entry = HistoryEntry(
        card_id=card.id,
        card_label=card.label,
        change_type=change_type,
        summary=summary,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/deck", response_model=schemas.DeckOut)
def get_deck(db: Session = Depends(get_db)) -> schemas.DeckOut:
    cards = db.scalars(select(Card).order_by(Card.order_index)).all()
    return schemas.DeckOut(
        suits=[schemas.SuitOut(code=s.code, label=s.label, symbol=s.symbol, color=s.color) for s in deck.SUITS],
        values=deck.VALUES,
        cards=[_to_card_out(c) for c in cards],
    )


@router.get("/cards/{card_id}", response_model=schemas.CardDetailOut)
def get_card(card_id: int, db: Session = Depends(get_db)) -> schemas.CardDetailOut:
    card = _get_card_or_404(db, card_id)
    return _to_card_detail(card)


@router.get("/cards/{card_id}/overlay.png")
def get_card_overlay(card_id: int, db: Session = Depends(get_db)) -> Response:
    card = _get_card_or_404(db, card_id)
    png_bytes = overlay.get_overlay_png_bytes(card.suit, card.value, card.joker_index)
    return Response(content=png_bytes, media_type="image/png", headers={"Cache-Control": "public, max-age=604800"})


@router.patch("/cards/{card_id}/description", response_model=schemas.CardDetailOut)
async def update_description(card_id: int, body: schemas.DescriptionUpdate, db: Session = Depends(get_db)) -> schemas.CardDetailOut:
    card = _get_card_or_404(db, card_id)
    old = card.description
    card.description = body.description
    card.description_customized = True
    db.commit()
    db.refresh(card)

    summary = f"Description modifiée pour « {card.label} »"
    entry = _log_history(db, card, "description", summary)

    result = _to_card_detail(card)
    await manager.broadcast(
        {
            "type": "card_updated",
            "card": result.model_dump(mode="json"),
            "history_entry": schemas.HistoryEntryOut.model_validate(entry).model_dump(mode="json"),
        }
    )
    return result


@router.post("/cards/{card_id}/images", response_model=schemas.CardDetailOut)
async def upload_image(card_id: int, file: UploadFile, db: Session = Depends(get_db)) -> schemas.CardDetailOut:
    card = _get_card_or_404(db, card_id)

    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Format d'image non supporté (jpeg, png, webp, gif uniquement)")

    data = await file.read()
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Image trop volumineuse (15 Mo maximum)")

    ext = EXT_BY_CONTENT_TYPE[content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = Path(config.UPLOADS_DIR) / filename
    dest.write_bytes(data)

    for img in card.images:
        img.is_current = False

    image = Image(
        card_id=card.id,
        filename=filename,
        original_filename=file.filename or filename,
        content_type=content_type,
        is_current=True,
    )
    db.add(image)
    db.commit()
    db.refresh(card)

    summary = f"Nouvelle image ajoutée pour « {card.label} »"
    entry = _log_history(db, card, "image", summary)

    result = _to_card_detail(card)
    await manager.broadcast(
        {
            "type": "card_updated",
            "card": result.model_dump(mode="json"),
            "history_entry": schemas.HistoryEntryOut.model_validate(entry).model_dump(mode="json"),
        }
    )
    return result


@router.put("/cards/{card_id}/images/{image_id}/activate", response_model=schemas.CardDetailOut)
async def activate_image(card_id: int, image_id: int, db: Session = Depends(get_db)) -> schemas.CardDetailOut:
    card = _get_card_or_404(db, card_id)
    target = db.get(Image, image_id)
    if target is None or target.card_id != card.id:
        raise HTTPException(status_code=404, detail="Image introuvable pour cette carte")

    for img in card.images:
        img.is_current = img.id == target.id
    db.commit()
    db.refresh(card)

    summary = f"Image précédente restaurée pour « {card.label} »"
    entry = _log_history(db, card, "image", summary)

    result = _to_card_detail(card)
    await manager.broadcast(
        {
            "type": "card_updated",
            "card": result.model_dump(mode="json"),
            "history_entry": schemas.HistoryEntryOut.model_validate(entry).model_dump(mode="json"),
        }
    )
    return result


@router.delete("/cards/{card_id}/images/{image_id}", response_model=schemas.CardDetailOut)
async def delete_image(card_id: int, image_id: int, db: Session = Depends(get_db)) -> schemas.CardDetailOut:
    card = _get_card_or_404(db, card_id)
    target = db.get(Image, image_id)
    if target is None or target.card_id != card.id:
        raise HTTPException(status_code=404, detail="Image introuvable pour cette carte")

    was_current = target.is_current
    filename = target.filename

    db.delete(target)
    db.flush()  # so card.images below no longer includes it

    if was_current:
        remaining = sorted(card.images, key=lambda i: i.uploaded_at, reverse=True)
        if remaining:
            remaining[0].is_current = True

    db.commit()
    db.refresh(card)

    # Best-effort: the DB row is already gone either way, so a missing or
    # locked file on disk shouldn't turn into a 500 for the user.
    try:
        (config.UPLOADS_DIR / filename).unlink(missing_ok=True)
    except OSError:
        pass

    summary = f"Image supprimée pour « {card.label} »"
    entry = _log_history(db, card, "image", summary)

    result = _to_card_detail(card)
    await manager.broadcast(
        {
            "type": "card_updated",
            "card": result.model_dump(mode="json"),
            "history_entry": schemas.HistoryEntryOut.model_validate(entry).model_dump(mode="json"),
        }
    )
    return result

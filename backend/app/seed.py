"""Database bootstrap: creates the 61 cards on first boot and (re)applies
default descriptions from default_description.md to any card a user
hasn't customized yet. Safe to call on every startup.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import config, deck
from .database import Base, engine
from .default_descriptions import parse_default_descriptions
from .models import Card

logger = logging.getLogger("deck.seed")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def ensure_cards(db: Session) -> None:
    existing = {(c.suit, c.value, c.joker_index) for c in db.scalars(select(Card))}
    created = 0
    for suit_code, value, joker_index, order_index in deck.iter_deck_definition():
        key = (suit_code, value, joker_index)
        if key in existing:
            continue
        db.add(
            Card(
                suit=suit_code,
                value=value,
                joker_index=joker_index,
                order_index=order_index,
                label=deck.card_label(suit_code, value, joker_index),
                description="",
                description_customized=False,
            )
        )
        created += 1
    if created:
        db.commit()
        logger.info("Seeded %d new card(s)", created)


def sync_default_descriptions(db: Session) -> None:
    by_card, by_joker = parse_default_descriptions(config.DEFAULT_DESCRIPTIONS_PATH)
    if not by_card and not by_joker:
        return
    updated = 0
    for card in db.scalars(select(Card).where(Card.description_customized.is_(False))):
        if card.value == deck.JOKER_VALUE:
            text = by_joker.get(card.joker_index or 0)
        else:
            text = by_card.get((card.suit, card.value))
        if text is not None and text != card.description:
            card.description = text
            updated += 1
    if updated:
        db.commit()
        logger.info("Synced default description(s) for %d card(s)", updated)


def bootstrap(db: Session) -> None:
    init_db()
    ensure_cards(db)
    sync_default_descriptions(db)

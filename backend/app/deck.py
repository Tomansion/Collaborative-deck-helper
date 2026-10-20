"""Static definition of the 5kings / Cinq Rois deck.

5 suits x 11 values (3..10, V, D, R) + 6 identical jokers = 61 cards.
This module is the single source of truth for suits/values ordering,
French labels and suit colors, used both for seeding the database and for
generating the colored overlays.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Suit:
    code: str  # internal identifier, used in the DB and API
    label: str  # French display name
    symbol: str  # unicode glyph drawn on the overlay
    color: str  # base hex color for the overlay algorithm


# Order matters: it drives the default display/grid order.
SUITS: list[Suit] = [
    Suit(code="coeur", label="Cœur", symbol="♥", color="#D7263D"),      # red
    Suit(code="carreau", label="Carreau", symbol="♦", color="#1D7FD9"),  # blue
    Suit(code="trefle", label="Trèfle", symbol="♣", color="#2E8B3D"),    # green
    Suit(code="pique", label="Pique", symbol="♠", color="#6C2EB9"),      # violet
    Suit(code="star", label="Star", symbol="★", color="#E0A800"),        # yellow
]
SUITS_BY_CODE: dict[str, Suit] = {s.code: s for s in SUITS}

# Card values, in rank order, from lowest to highest.
VALUES: list[str] = ["3", "4", "5", "6", "7", "8", "9", "10", "V", "D", "R"]
VALUE_LABELS: dict[str, str] = {
    "3": "3", "4": "4", "5": "5", "6": "6", "7": "7",
    "8": "8", "9": "9", "10": "10",
    "V": "Valet", "D": "Dame", "R": "Roi",
}
COURT_VALUES = {"V", "D", "R"}

JOKER_VALUE = "JOKER"
JOKER_COUNT = 6


def value_rank(value: str) -> int:
    """Index of a value within VALUES (0 = lowest, len-1 = highest)."""
    return VALUES.index(value)


def card_label(suit_code: str | None, value: str, joker_index: int | None = None) -> str:
    """Human readable French label for a card, e.g. 'Roi de Cœur'."""
    if value == JOKER_VALUE:
        return f"Joker n°{joker_index}"
    suit = SUITS_BY_CODE[suit_code]
    value_label = VALUE_LABELS[value]
    return f"{value_label} de {suit.label}"


def iter_deck_definition():
    """Yield (suit_code, value, joker_index, order_index) for all 61 cards."""
    order_index = 0
    for suit in SUITS:
        for value in VALUES:
            yield suit.code, value, None, order_index
            order_index += 1
    for joker_index in range(1, JOKER_COUNT + 1):
        yield None, JOKER_VALUE, joker_index, order_index
        order_index += 1

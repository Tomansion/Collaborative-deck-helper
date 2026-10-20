"""Parsing of ``default_description.md``, the seed content for card
descriptions on first boot (see Spec.md).

Format: a markdown table with one row per value (3..10, V, D, R) and one
column per suit, plus an optional "## Jokers" section with one line per
joker. Suit column headers are matched leniently (accents/typos-tolerant)
against the suits defined in deck.py, so small spelling variations in the
authoring spreadsheet don't break the import.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from . import deck


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", text.lower())


_SUIT_ALIASES: dict[str, str] = {}
for suit in deck.SUITS:
    _SUIT_ALIASES[_normalize(suit.label)] = suit.code
    _SUIT_ALIASES[_normalize(suit.code)] = suit.code
# Common typos/variants seen in the source spreadsheet.
_SUIT_ALIASES.update(
    {
        _normalize("Careau"): "carreau",
        _normalize("Pic"): "pique",
        _normalize("Etoile"): "star",
        _normalize("Étoile"): "star",
    }
)


def _match_suit(header: str) -> str | None:
    return _SUIT_ALIASES.get(_normalize(header))


def _match_value(cell: str) -> str | None:
    cell = cell.strip()
    normalized = _normalize(cell)
    for value in deck.VALUES:
        if _normalize(value) == normalized:
            return value
    aliases = {"valet": "V", "dame": "D", "roi": "R"}
    return aliases.get(normalized)


def parse_default_descriptions(path: Path) -> tuple[dict[tuple[str, str], str], dict[int, str]]:
    """Returns ((suit_code, value) -> text, joker_index -> text)."""
    by_card: dict[tuple[str, str], str] = {}
    by_joker: dict[int, str] = {}

    if not path.exists():
        return by_card, by_joker

    lines = path.read_text(encoding="utf-8").splitlines()

    in_jokers_section = False
    header_suits: list[str | None] | None = None
    joker_index = 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#"):
            in_jokers_section = "joker" in _normalize(line)
            header_suits = None
            continue

        if in_jokers_section:
            # Jokers are a plain markdown list ("1. text"), not a table
            # row, so this must be handled before the "|" check below.
            joker_index += 1
            text = re.sub(r"^(\d+[.)]|[-*])\s*", "", line).strip()
            if text:
                by_joker[joker_index] = text
            continue

        if not line.startswith("|"):
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]

        if header_suits is None:
            # First table row encountered is the header.
            header_suits = [_match_suit(c) for c in cells[1:]]
            continue

        if set("".join(cells)) <= {"-", " "}:
            continue  # markdown table separator row, e.g. |---|---|

        value = _match_value(cells[0])
        if value is None:
            continue
        for suit_code, text in zip(header_suits, cells[1:]):
            if suit_code and text:
                by_card[(suit_code, value)] = text

    return by_card, by_joker

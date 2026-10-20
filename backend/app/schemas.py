from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SuitOut(BaseModel):
    code: str
    label: str
    symbol: str
    color: str


class ImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    original_filename: str
    uploaded_at: datetime
    is_current: bool


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    suit: str | None
    value: str
    joker_index: int | None
    order_index: int
    label: str
    description: str
    overlay_url: str
    current_image: ImageOut | None
    image_count: int


class CardDetailOut(CardOut):
    images: list[ImageOut]


class DescriptionUpdate(BaseModel):
    description: str


class HistoryEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_id: int
    card_label: str
    change_type: str
    summary: str
    created_at: datetime


class DeckOut(BaseModel):
    suits: list[SuitOut]
    values: list[str]
    cards: list[CardOut]

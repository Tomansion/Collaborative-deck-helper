from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer

# All datetimes are stored naive in the DB but always *mean* UTC (see
# models.utcnow). Serialize them with an explicit UTC offset so the
# frontend's `new Date(...)` never misinterprets them as local time.
UtcDateTime = Annotated[
    datetime,
    PlainSerializer(lambda dt: dt.replace(tzinfo=timezone.utc).isoformat(), return_type=str, when_used="json"),
]


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
    uploaded_at: UtcDateTime
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
    created_at: UtcDateTime


class DeckOut(BaseModel):
    suits: list[SuitOut]
    values: list[str]
    cards: list[CardOut]

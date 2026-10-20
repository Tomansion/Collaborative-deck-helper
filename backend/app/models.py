from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    suit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    value: Mapped[str] = mapped_column(String(8))
    joker_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, index=True)
    label: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    # Set to True the first time a user edits the description via the API.
    # Default-description sync (from default_description.md) only ever
    # touches cards where this is still False, so it never clobbers an
    # edit a user made -- even if they cleared the text back to empty.
    description_customized: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    images: Mapped[list["Image"]] = relationship(
        back_populates="card",
        order_by="Image.uploaded_at",
        cascade="all, delete-orphan",
    )

    @property
    def current_image(self) -> "Image | None":
        for image in self.images:
            if image.is_current:
                return image
        return None


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(64))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    card: Mapped["Card"] = relationship(back_populates="images")


class HistoryEntry(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), index=True)
    card_label: Mapped[str] = mapped_column(String(64))
    change_type: Mapped[str] = mapped_column(String(32))  # 'description' | 'image'
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

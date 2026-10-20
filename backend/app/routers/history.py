from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import HistoryEntry

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=list[schemas.HistoryEntryOut])
def get_history(limit: int = 200, db: Session = Depends(get_db)) -> list[schemas.HistoryEntryOut]:
    entries = db.scalars(
        select(HistoryEntry).order_by(HistoryEntry.created_at.desc()).limit(min(limit, 1000))
    ).all()
    return [schemas.HistoryEntryOut.model_validate(e) for e in entries]

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.music import ScoreContentSchema


class ScoreCreate(BaseModel):
    title: str
    composer: str = ""
    content: ScoreContentSchema


class ScoreUpdate(BaseModel):
    title: Optional[str] = None
    composer: Optional[str] = None
    content: Optional[ScoreContentSchema] = None


class ScoreListItem(BaseModel):
    id: int
    title: str
    composer: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScoreRead(BaseModel):
    id: int
    title: str
    composer: str
    created_at: datetime
    updated_at: datetime
    content: ScoreContentSchema

    class Config:
        from_attributes = True

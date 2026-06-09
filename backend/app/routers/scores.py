from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.music import ScoreContentSchema
from app.schemas.score import ScoreCreate, ScoreListItem, ScoreRead, ScoreUpdate
from app.services import score_service
from app.services.validation import validate_score
from app.services.score_service import schema_to_model

router = APIRouter(prefix="/api/scores", tags=["scores"])


@router.get("", response_model=list[ScoreListItem])
def list_scores(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return score_service.list_scores(db, skip=skip, limit=limit)


@router.post("", response_model=ScoreRead, status_code=201)
def create_score(data: ScoreCreate, db: Session = Depends(get_db)):
    record = score_service.create_score(db, data)
    content = ScoreContentSchema.model_validate_json(record.content_json)
    return ScoreRead(
        id=record.id,
        title=record.title,
        composer=record.composer,
        created_at=record.created_at,
        updated_at=record.updated_at,
        content=content,
    )


@router.get("/{score_id}", response_model=ScoreRead)
def get_score(score_id: int, db: Session = Depends(get_db)):
    record = score_service.get_score(db, score_id)
    if not record:
        raise HTTPException(status_code=404, detail="Score not found")
    content = ScoreContentSchema.model_validate_json(record.content_json)
    return ScoreRead(
        id=record.id,
        title=record.title,
        composer=record.composer,
        created_at=record.created_at,
        updated_at=record.updated_at,
        content=content,
    )


@router.put("/{score_id}", response_model=ScoreRead)
def update_score(score_id: int, data: ScoreUpdate, db: Session = Depends(get_db)):
    record = score_service.update_score(db, score_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Score not found")
    content = ScoreContentSchema.model_validate_json(record.content_json)
    return ScoreRead(
        id=record.id,
        title=record.title,
        composer=record.composer,
        created_at=record.created_at,
        updated_at=record.updated_at,
        content=content,
    )


@router.delete("/{score_id}", status_code=204)
def delete_score(score_id: int, db: Session = Depends(get_db)):
    if not score_service.delete_score(db, score_id):
        raise HTTPException(status_code=404, detail="Score not found")


@router.post("/{score_id}/validate")
def validate(score_id: int, db: Session = Depends(get_db)):
    record = score_service.get_score(db, score_id)
    if not record:
        raise HTTPException(status_code=404, detail="Score not found")
    content = ScoreContentSchema.model_validate_json(record.content_json)
    score = schema_to_model(content)
    errors = validate_score(score)
    return {"valid": len(errors) == 0, "errors": errors}

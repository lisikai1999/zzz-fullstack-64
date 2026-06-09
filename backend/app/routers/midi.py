from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.music import ScoreContentSchema
from app.services import score_service
from app.services.midi_generator import generate_midi
from app.services.score_service import schema_to_model

router = APIRouter(prefix="/api/scores", tags=["midi"])


@router.get("/{score_id}/midi")
def download_midi(
    score_id: int,
    metronome: bool = Query(False),
    start: int = Query(1, ge=1),
    end: int | None = Query(None),
    db: Session = Depends(get_db),
):
    record = score_service.get_score(db, score_id)
    if not record:
        raise HTTPException(status_code=404, detail="Score not found")

    content = ScoreContentSchema.model_validate_json(record.content_json)
    score = schema_to_model(content)

    midi_bytes = generate_midi(
        score,
        include_metronome=metronome,
        start_measure=start,
        end_measure=end,
    )

    filename = f"{score.title.replace(' ', '_')}.mid"
    return Response(
        content=midi_bytes,
        media_type="audio/midi",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

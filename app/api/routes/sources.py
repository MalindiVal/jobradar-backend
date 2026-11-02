from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Source
from app.schemas import SourceRead, SourcePatch

router = APIRouter(prefix="/sources", tags=["sources"])

@router.get("", response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_db)):
    return list(db.scalars(select(Source).order_by(Source.name)))

@router.patch("/{source_id}", response_model=SourceRead)
def patch_source(source_id: int, payload: SourcePatch, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source: raise HTTPException(404, "Source introuvable")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    db.commit(); db.refresh(source)
    return source

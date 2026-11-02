from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SearchProfile
from app.schemas import ProfileRead, ProfileUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/profile", response_model=ProfileRead)
def get_profile(db: Session = Depends(get_db)):
    profile = db.scalar(select(SearchProfile).limit(1))
    if profile is None:
        profile = SearchProfile(); db.add(profile); db.commit(); db.refresh(profile)
    return profile

@router.put("/profile", response_model=ProfileRead)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.scalar(select(SearchProfile).limit(1))
    if profile is None:
        profile = SearchProfile(); db.add(profile)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.commit(); db.refresh(profile)
    return profile

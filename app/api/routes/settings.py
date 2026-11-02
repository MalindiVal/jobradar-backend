from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ProfileRead, ProfileUpdate
from app.services.offers import get_or_create_profile

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/profile", response_model=ProfileRead)
def get_profile(db: Session = Depends(get_db)):
    return get_or_create_profile(db)

@router.put("/profile", response_model=ProfileRead)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.commit(); db.refresh(profile)
    return profile

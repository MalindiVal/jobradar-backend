from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ProfileRead, ProfileUpdate
from app.services.offers import get_or_create_preferences, get_or_create_profile, set_profile_skills

router = APIRouter(prefix="/settings", tags=["settings"])

# La réponse combine les critères de recherche (search_preferences) et les compétences
# du profil professionnel (profiles / profile_skills), pour garder le format attendu par le frontend.

def _read(db: Session) -> ProfileRead:
    preferences, profile = get_or_create_preferences(db), get_or_create_profile(db)
    return ProfileRead(id=preferences.id, name=preferences.name, keywords=preferences.keywords,
                       locations=preferences.locations, skills=profile.skills,
                       duration_months=preferences.duration_months, contract_type=preferences.contract_type)

@router.get("/profile", response_model=ProfileRead)
def get_profile(db: Session = Depends(get_db)):
    return _read(db)

@router.put("/profile", response_model=ProfileRead)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)):
    preferences, profile = get_or_create_preferences(db), get_or_create_profile(db)
    data = payload.model_dump()
    set_profile_skills(db, profile, data.pop("skills"))
    for key, value in data.items():
        setattr(preferences, key, value)
    db.commit()
    db.expire_all()
    return _read(db)

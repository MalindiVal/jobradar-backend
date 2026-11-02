from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Offer, OfferSkill, SearchProfile, Source
from app.services.dedup import dedup_key

def get_or_create_profile(db: Session) -> SearchProfile:
    profile = db.scalar(select(SearchProfile).limit(1))
    if profile is None:
        profile = SearchProfile(); db.add(profile); db.commit(); db.refresh(profile)
    return profile

def get_or_create_source(db: Session, name: str) -> Source:
    name = (name or "manual").strip().lower() or "manual"
    source = db.scalar(select(Source).where(Source.name == name))
    if source is None:
        source = Source(name=name, label=name.capitalize()); db.add(source); db.flush()
    return source

def normalize_skills(skills) -> list[str]:
    seen, result = set(), []
    for skill in skills or []:
        skill = str(skill).strip()
        if skill and skill.lower() not in seen:
            seen.add(skill.lower()); result.append(skill)
    return result

def find_existing(db: Session, item: dict) -> tuple[str, Offer | None]:
    key = dedup_key(item)
    return key, db.scalar(select(Offer).where(Offer.deduplication_key == key))

def build_offer(db: Session, item: dict, key: str, score: int, explanation: str) -> Offer:
    fields = {k: v for k, v in item.items() if k not in ("source", "skills")}
    offer = Offer(**fields, source_ref=get_or_create_source(db, item.get("source")),
                  deduplication_key=key, match_score=score, match_explanation=explanation)
    offer.skill_links = [OfferSkill(name) for name in normalize_skills(item.get("skills"))]
    db.add(offer)
    return offer

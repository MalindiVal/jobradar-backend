import re
from types import SimpleNamespace
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import JobOffer, OfferSkill, Profile, ProfileSkill, SearchPreference, Skill, JobSource
from app.services.dedup import dedup_key

def get_or_create_preferences(db: Session) -> SearchPreference:
    preferences = db.scalar(select(SearchPreference).order_by(SearchPreference.id).limit(1))
    if preferences is None:
        preferences = SearchPreference(); db.add(preferences); db.commit(); db.refresh(preferences)
    return preferences

def get_or_create_profile(db: Session) -> Profile:
    profile = db.scalar(select(Profile).order_by(Profile.id).limit(1))
    if profile is None:
        profile = Profile(); db.add(profile); db.commit(); db.refresh(profile)
    return profile

def get_matching_criteria(db: Session) -> SimpleNamespace:
    """Critères utilisés par le scoring par règles : préférences de recherche + compétences du profil."""
    preferences, profile = get_or_create_preferences(db), get_or_create_profile(db)
    return SimpleNamespace(keywords=preferences.keywords, locations=preferences.locations,
                           duration_months=preferences.duration_months, contract_type=preferences.contract_type,
                           skills=profile.skills)

def normalize_skill_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name)).strip().lower()

def get_or_create_skill(db: Session, name: str) -> Skill:
    normalized = normalize_skill_name(name)
    skill = db.scalar(select(Skill).where(Skill.normalized_name == normalized))
    if skill is None:
        skill = Skill(name=re.sub(r"\s+", " ", str(name)).strip(), normalized_name=normalized)
        db.add(skill); db.flush()
    return skill

def set_profile_skills(db: Session, profile: Profile, names: list[str]) -> None:
    profile.skill_links = [ProfileSkill(skill=get_or_create_skill(db, name)) for name in normalize_skills(names)]

def get_or_create_source(db: Session, name: str) -> JobSource:
    name = (name or "manual").strip().lower() or "manual"
    source = db.scalar(select(JobSource).where(JobSource.name == name))
    if source is None:
        source = JobSource(name=name, label=name.capitalize()); db.add(source); db.flush()
    return source

def normalize_skills(skills) -> list[str]:
    seen, result = set(), []
    for skill in skills or []:
        skill = str(skill).strip()
        if skill and skill.lower() not in seen:
            seen.add(skill.lower()); result.append(skill)
    return result

def find_existing(db: Session, item: dict) -> tuple[str, JobOffer | None]:
    """Doublon si (source, external_id) est déjà connu, sinon si l'empreinte correspond."""
    key = dedup_key(item)
    external_id = (item.get("external_id") or "").strip()
    if external_id:
        source = db.scalar(select(JobSource).where(JobSource.name == (item.get("source") or "manual").strip().lower()))
        if source is not None:
            existing = db.scalar(select(JobOffer).where(JobOffer.source_id == source.id,
                                                        JobOffer.external_id == external_id))
            if existing is not None:
                return key, existing
    return key, db.scalar(select(JobOffer).where(JobOffer.deduplication_key == key))

def build_offer(db: Session, item: dict, key: str, score: int, explanation: str) -> JobOffer:
    fields = {k: v for k, v in item.items() if k not in ("source", "skills")}
    if fields.get("external_id") is not None:
        fields["external_id"] = fields["external_id"].strip() or None
    offer = JobOffer(**fields, source_ref=get_or_create_source(db, item.get("source")),
                     deduplication_key=key, match_score=score, match_explanation=explanation)
    offer.skill_links = [OfferSkill(name) for name in normalize_skills(item.get("skills"))]
    db.add(offer)
    return offer

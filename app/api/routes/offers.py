from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Offer, SearchProfile
from app.schemas import OfferCreate, OfferRead, OfferPatch
from app.services.collector import dedup_key
from app.services.scoring import score_offer

router = APIRouter(prefix="/offers", tags=["offers"])

@router.get("", response_model=list[OfferRead])
def list_offers(q: str | None = None, min_score: int = Query(0, ge=0, le=100), db: Session = Depends(get_db)):
    stmt = select(Offer).where(Offer.match_score >= min_score).order_by(desc(Offer.first_seen_at))
    offers = list(db.scalars(stmt))
    if q:
        needle = q.lower()
        offers = [o for o in offers if needle in f"{o.title} {o.company} {o.location} {o.description}".lower()]
    return offers

@router.get("/{offer_id}", response_model=OfferRead)
def get_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = db.get(Offer, offer_id)
    if not offer: raise HTTPException(404, "Offre introuvable")
    return offer

@router.post("", response_model=OfferRead, status_code=201)
def create_offer(payload: OfferCreate, db: Session = Depends(get_db)):
    item = payload.model_dump()
    key = dedup_key(item)
    existing = db.scalar(select(Offer).where(Offer.deduplication_key == key))
    if existing: return existing
    profile = db.scalar(select(SearchProfile).limit(1))
    if profile is None:
        profile = SearchProfile(); db.add(profile); db.commit(); db.refresh(profile)
    score, explanation = score_offer(item, profile)
    offer = Offer(**item, deduplication_key=key, match_score=score, match_explanation=explanation)
    db.add(offer); db.commit(); db.refresh(offer)
    return offer

@router.patch("/{offer_id}", response_model=OfferRead)
def patch_offer(offer_id: int, payload: OfferPatch, db: Session = Depends(get_db)):
    offer = db.get(Offer, offer_id)
    if not offer: raise HTTPException(404, "Offre introuvable")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(offer, key, value)
    db.commit(); db.refresh(offer)
    return offer

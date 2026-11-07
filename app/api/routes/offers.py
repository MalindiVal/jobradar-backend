from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import JobOffer
from app.schemas import OfferCreate, OfferRead, OfferPatch
from app.services.offers import get_matching_criteria, find_existing, build_offer
from app.services.scoring import score_offer

router = APIRouter(prefix="/offers", tags=["offers"])

@router.get("", response_model=list[OfferRead])
def list_offers(q: str | None = None, min_score: int = Query(0, ge=0, le=100), db: Session = Depends(get_db)):
    stmt = select(JobOffer).where(JobOffer.match_score >= min_score).order_by(desc(JobOffer.first_seen_at))
    offers = list(db.scalars(stmt).unique())
    if q:
        needle = q.lower()
        offers = [o for o in offers if needle in f"{o.title} {o.company} {o.location} {o.description}".lower()]
    return offers

@router.get("/{offer_id}", response_model=OfferRead)
def get_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = db.get(JobOffer, offer_id)
    if not offer: raise HTTPException(404, "Offre introuvable")
    return offer

@router.post("", response_model=OfferRead, status_code=201)
def create_offer(payload: OfferCreate, db: Session = Depends(get_db)):
    item = payload.model_dump()
    key, existing = find_existing(db, item)
    if existing: return existing
    score, explanation = score_offer(item, get_matching_criteria(db))
    offer = build_offer(db, item, key, score, explanation)
    db.commit(); db.refresh(offer)
    return offer

@router.patch("/{offer_id}", response_model=OfferRead)
def patch_offer(offer_id: int, payload: OfferPatch, db: Session = Depends(get_db)):
    offer = db.get(JobOffer, offer_id)
    if not offer: raise HTTPException(404, "Offre introuvable")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(offer, key, value)
    db.commit(); db.refresh(offer)
    return offer

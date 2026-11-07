from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Application, JobOffer
from app.schemas import ApplicationCreate, ApplicationPatch, ApplicationRead

router = APIRouter(prefix="/applications", tags=["applications"])

def _apply_status(application: Application, status: str):
    application.status = status
    if status == "APPLIED" and application.applied_at is None:
        application.applied_at = datetime.now(timezone.utc)

@router.get("", response_model=list[ApplicationRead])
def list_applications(status: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Application).order_by(desc(Application.updated_at))
    if status:
        stmt = stmt.where(Application.status == status)
    return list(db.scalars(stmt).unique())

@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(application_id: int, db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application: raise HTTPException(404, "Candidature introuvable")
    return application

@router.post("", response_model=ApplicationRead, status_code=201)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    if not db.get(JobOffer, payload.offer_id): raise HTTPException(404, "Offre introuvable")
    if db.scalar(select(Application).where(Application.offer_id == payload.offer_id)):
        raise HTTPException(409, "Une candidature existe déjà pour cette offre")
    application = Application(offer_id=payload.offer_id, notes=payload.notes, applied_at=payload.applied_at)
    _apply_status(application, payload.status)
    db.add(application); db.commit(); db.refresh(application)
    return application

@router.patch("/{application_id}", response_model=ApplicationRead)
def patch_application(application_id: int, payload: ApplicationPatch, db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application: raise HTTPException(404, "Candidature introuvable")
    data = payload.model_dump(exclude_unset=True)
    status = data.pop("status", None)
    for key, value in data.items():
        setattr(application, key, value)
    if status:
        _apply_status(application, status)
    db.commit(); db.refresh(application)
    return application

@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application: raise HTTPException(404, "Candidature introuvable")
    db.delete(application); db.commit()
    return Response(status_code=204)

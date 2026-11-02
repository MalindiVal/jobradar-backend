from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CollectionLog
from app.schemas import CollectionLogRead
from app.services.collector import run_collection

router = APIRouter(prefix="/collection", tags=["collection"])

@router.post("/run")
async def trigger_collection():
    return await run_collection()

@router.get("/runs", response_model=list[CollectionLogRead])
def list_runs(db: Session = Depends(get_db)):
    return list(db.scalars(select(CollectionLog).order_by(desc(CollectionLog.started_at)).limit(50)))

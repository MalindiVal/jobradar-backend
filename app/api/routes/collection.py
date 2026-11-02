from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CollectionRun
from app.services.collector import run_collection

router = APIRouter(prefix="/collection", tags=["collection"])

@router.post("/run")
async def trigger_collection():
    return await run_collection()

@router.get("/runs")
def list_runs(db: Session = Depends(get_db)):
    return list(db.scalars(select(CollectionRun).order_by(desc(CollectionRun.started_at)).limit(50)))

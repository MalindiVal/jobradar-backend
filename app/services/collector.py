import hashlib
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Offer, SearchProfile, CollectionRun, Notification
from app.core.config import settings
from app.services.collection.registry import get_connectors
from app.services.scoring import score_offer
from app.services.ai import explain_with_ai
from app.services.notifications import send_offer_email

def dedup_key(item: dict) -> str:
    canonical = (item.get("source_url") or "").strip().lower().rstrip("/")
    if not canonical:
        canonical = "|".join(str(item.get(k, "")).lower().strip() for k in ("title", "company", "location"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

async def run_collection():
    db = SessionLocal()
    summary = {"sources": [], "found": 0, "new": 0}
    try:
        profile = db.scalar(select(SearchProfile).limit(1))
        if profile is None:
            profile = SearchProfile()
            db.add(profile)
            db.commit()
            db.refresh(profile)
        for connector in get_connectors(settings.source_list):
            run = CollectionRun(source=connector.name, status="running")
            db.add(run); db.commit(); db.refresh(run)
            try:
                items = await connector.search_jobs({"profile": profile})
                new_count = 0
                for item in items:
                    summary["found"] += 1
                    key = dedup_key(item)
                    if db.scalar(select(Offer).where(Offer.deduplication_key == key)):
                        continue
                    score, explanation = score_offer(item, profile)
                    ai_explanation = await explain_with_ai(item, score)
                    if ai_explanation:
                        explanation = f"{explanation} Analyse complémentaire : {ai_explanation}"
                    offer = Offer(**item, deduplication_key=key, match_score=score, match_explanation=explanation)
                    db.add(offer); db.commit(); db.refresh(offer)
                    new_count += 1; summary["new"] += 1
                    if score >= 60:
                        ok, error = send_offer_email(offer)
                        db.add(Notification(offer_id=offer.id, status="sent" if ok else "skipped" if error == "SMTP non configuré" else "failed",
                                            recipient=settings.smtp_to, error_message=error))
                        db.commit()
                run.status = "success"; run.found_count = len(items); run.new_count = new_count
            except Exception as exc:
                run.status = "failed"; run.error_message = str(exc)
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            summary["sources"].append({"source": connector.name, "status": run.status, "new": run.new_count})
        return summary
    finally:
        db.close()

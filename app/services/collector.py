from datetime import datetime, timezone
from app.database import SessionLocal
from app.models import CollectionLog, Notification
from app.core.config import settings
from app.services.collection.registry import get_connectors
from app.services.offers import get_or_create_profile, get_or_create_source, find_existing, build_offer
from app.services.scoring import score_offer
from app.services.ai import explain_with_ai
from app.services.notifications import send_offer_email

async def run_collection():
    db = SessionLocal()
    summary = {"sources": [], "found": 0, "new": 0}
    try:
        profile = get_or_create_profile(db)
        for connector in get_connectors(settings.source_list):
            source = get_or_create_source(db, connector.name)
            db.commit()
            if not source.is_enabled:
                continue
            run = CollectionLog(source=connector.name, status="running")
            db.add(run); db.commit(); db.refresh(run)
            try:
                items = await connector.search_jobs({"profile": profile})
                new_count = 0
                for item in items:
                    summary["found"] += 1
                    key, existing = find_existing(db, item)
                    if existing:
                        continue
                    score, explanation = score_offer(item, profile)
                    ai_explanation = await explain_with_ai(item, score)
                    if ai_explanation:
                        explanation = f"{explanation} Analyse complémentaire : {ai_explanation}"
                    offer = build_offer(db, item, key, score, explanation)
                    db.commit(); db.refresh(offer)
                    new_count += 1; summary["new"] += 1
                    if score >= 60:
                        ok, error = send_offer_email(offer)
                        db.add(Notification(offer_id=offer.id, status="sent" if ok else "skipped" if error == "SMTP non configuré" else "failed",
                                            recipient=settings.smtp_to, error_message=error))
                        db.commit()
                run.status = "success"; run.found_count = len(items); run.new_count = new_count
            except Exception as exc:
                db.rollback()
                run.status = "failed"; run.error_message = str(exc)
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            summary["sources"].append({"source": connector.name, "status": run.status, "new": run.new_count})
        return summary
    finally:
        db.close()

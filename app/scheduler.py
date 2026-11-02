from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings
from app.services.collector import run_collection

scheduler = AsyncIOScheduler()

def start_scheduler():
    if settings.scheduler_enabled:
        scheduler.add_job(run_collection, "interval", minutes=max(5, settings.collection_interval_minutes),
                          id="hourly-collection", replace_existing=True, max_instances=1)
        scheduler.start()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)

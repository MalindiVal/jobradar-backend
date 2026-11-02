from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import offers, settings as settings_routes, collection, sources, applications
from app.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(offers.router, prefix="/api")
app.include_router(settings_routes.router, prefix="/api")
app.include_router(collection.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(applications.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}

from fastapi import APIRouter, Depends
from app.core.security import require_internal_key

# Routes réservées à n8n (jalon 2 : upsert des offres, analyse, rapports de collecte).
router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[Depends(require_internal_key)])

@router.get("/ping")
def ping():
    """Permet à n8n de vérifier l'accès à l'API et la validité de la clé interne."""
    return {"status": "ok"}

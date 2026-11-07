import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_internal_key(api_key: str | None = Security(_api_key_header)) -> None:
    """Protège les routes /internal, réservées à n8n et aux services autorisés."""
    expected = settings.jobradar_internal_key
    if not expected:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "JOBRADAR_INTERNAL_KEY non configurée")
    if not api_key or not secrets.compare_digest(api_key.encode(), expected.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clé interne invalide")

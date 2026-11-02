import hashlib
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

# Paramètres de suivi/navigation qui ne changent pas l'offre désignée par l'URL.
TRACKING_PARAMS = {
    "gclid", "fbclid", "msclkid", "dclid", "yclid", "mc_cid", "mc_eid", "_hsenc", "_hsmi", "xtor",
    "ref", "ref_src", "refid", "referer", "referrer", "trk", "trkinfo", "trackingid", "lipi",
    "position", "pagenum", "from", "src", "sid", "session", "sessionid",
}

def _is_tracking_param(name: str) -> bool:
    name = name.lower()
    return name.startswith("utm_") or name in TRACKING_PARAMS

def canonicalize_url(url: str | None) -> str:
    """URL canonique : schéma https, hôte en minuscules sans www ni port par défaut,
    sans fragment, sans paramètres de suivi, paramètres restants triés, sans / final."""
    url = (url or "").strip()
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if parts.port and parts.port not in (80, 443):
        host = f"{host}:{parts.port}"
    path = re.sub(r"/{2,}", "/", parts.path).rstrip("/")
    query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _is_tracking_param(k))
    return urlunsplit(("https", host, path, urlencode(query), ""))

def _normalize_text(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().lower()

def offer_fingerprint(item: dict) -> str:
    return "|".join(_normalize_text(item.get(k)) for k in ("title", "company", "location"))

def _url_identifies_offer(canonical: str) -> bool:
    # Une URL sans chemin ni paramètre (ex. page d'accueil carrières) ne désigne pas une offre précise.
    parts = urlsplit(canonical)
    return bool(parts.path.strip("/") or parts.query)

def dedup_key(item: dict) -> str:
    """Identifiant stable d'une offre : URL canonique, complétée par l'empreinte
    titre/entreprise/localisation lorsque l'URL est absente ou trop générique."""
    canonical = canonicalize_url(item.get("source_url"))
    if canonical and _url_identifies_offer(canonical):
        basis = canonical
    else:
        basis = f"{canonical}|{offer_fingerprint(item)}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()

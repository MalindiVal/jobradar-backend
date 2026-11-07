OFFER = {
    "title": "Alternant Développeur Full Stack",
    "company": "Entreprise Exemple",
    "location": "Dijon",
    "duration_months": 36,
    "skills": ["React", "TypeScript", "Python", "SQL", "react"],
    "source": "LinkedIn",
    "source_url": "https://www.linkedin.com/jobs/view/123?trackingId=abc",
}

def test_health(client):
    assert client.get("/health").json()["status"] == "ok"

def test_create_offer_stores_source_and_skills(client):
    offer = client.post("/api/offers", json=OFFER).json()
    assert offer["source"] == "linkedin"
    assert offer["skills"] == ["React", "TypeScript", "Python", "SQL"]
    assert offer["status"] == "NEW"
    assert [s["name"] for s in client.get("/api/sources").json()] == ["linkedin"]

def test_same_offer_with_other_tracking_is_deduplicated(client):
    first = client.post("/api/offers", json=OFFER).json()
    second = client.post("/api/offers", json={**OFFER, "source_url": "https://linkedin.com/jobs/view/123/?utm_source=mail"}).json()
    assert first["id"] == second["id"]
    assert len(client.get("/api/offers").json()) == 1

def test_application_lifecycle(client):
    offer_id = client.post("/api/offers", json=OFFER).json()["id"]
    created = client.post("/api/applications", json={"offer_id": offer_id})
    assert created.status_code == 201
    app_id = created.json()["id"]
    assert client.post("/api/applications", json={"offer_id": offer_id}).status_code == 409
    patched = client.patch(f"/api/applications/{app_id}", json={"status": "APPLIED", "notes": "Envoyé"}).json()
    assert patched["status"] == "APPLIED" and patched["applied_at"] is not None
    assert patched["offer"]["id"] == offer_id
    assert client.patch(f"/api/applications/{app_id}", json={"status": "FOO"}).status_code == 422
    assert client.delete(f"/api/applications/{app_id}").status_code == 204
    assert client.get("/api/applications").json() == []

def test_application_url_is_exposed_with_legacy_alias(client):
    payload = {k: v for k, v in OFFER.items() if k != "source_url"} | {"application_url": "https://example.com/o/1"}
    offer = client.post("/api/offers", json=payload).json()
    assert offer["application_url"] == offer["source_url"] == "https://example.com/o/1"
    assert offer["analysis_status"] == "pending_analysis"

def test_same_source_and_external_id_is_deduplicated(client):
    base = {"title": "Alternant Data", "source": "la_bonne_alternance", "external_id": "LBA-1"}
    first = client.post("/api/offers", json={**base, "application_url": "https://example.com/a"}).json()
    # URL différente mais même identifiant externe : même offre.
    second = client.post("/api/offers", json={**base, "application_url": "https://example.com/b"}).json()
    assert first["id"] == second["id"] and first["external_id"] == "LBA-1"
    # Même identifiant externe sur une autre source : offre distincte.
    other = client.post("/api/offers", json={**base, "source": "france_travail", "application_url": "https://example.com/c"}).json()
    assert other["id"] != first["id"]

def test_profile_settings_store_skills_on_profile(client):
    payload = {"name": "Recherche", "keywords": ["backend"], "locations": ["Dijon"],
               "skills": ["Python", "python", " FastAPI "], "duration_months": 24, "contract_type": "Alternance"}
    saved = client.put("/api/settings/profile", json=payload).json()
    assert saved["skills"] == ["Python", "FastAPI"]
    assert client.put("/api/settings/profile", json={**payload, "skills": ["Docker"]}).json()["skills"] == ["Docker"]
    assert client.get("/api/settings/profile").json()["duration_months"] == 24

def test_internal_routes_require_api_key(client):
    assert client.get("/internal/ping").status_code == 401
    assert client.get("/internal/ping", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/internal/ping", headers={"X-API-Key": "test-internal-key"}).json() == {"status": "ok"}

def test_internal_routes_refused_without_configured_key(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "jobradar_internal_key", "")
    assert client.get("/internal/ping", headers={"X-API-Key": ""}).status_code == 503

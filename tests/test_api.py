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

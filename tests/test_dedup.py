from app.services.dedup import canonicalize_url, dedup_key

def test_same_url_has_same_key():
    a = {"source_url": "https://example.com/job/1"}
    b = {"source_url": "https://example.com/job/1/"}
    assert dedup_key(a) == dedup_key(b)

def test_canonical_url_drops_tracking_and_normalizes_host():
    url = "http://WWW.LinkedIn.com/jobs/view/123/?utm_source=mail&trackingId=abc&refId=x#top"
    assert canonicalize_url(url) == "https://linkedin.com/jobs/view/123"

def test_canonical_url_keeps_identifying_params_sorted():
    assert canonicalize_url("https://fr.indeed.com/viewjob?jk=42&from=serp&b=1") == "https://fr.indeed.com/viewjob?b=1&jk=42"

def test_generic_url_is_completed_by_fingerprint():
    base = {"source_url": "https://entreprise.fr/", "company": "Entreprise", "location": "Dijon"}
    assert dedup_key({**base, "title": "Alternant Dev"}) != dedup_key({**base, "title": "Alternant Data"})

def test_missing_url_uses_normalized_fingerprint():
    a = {"title": "Développeur  Full Stack", "company": "ACME", "location": "Dijon"}
    b = {"title": "developpeur full stack", "company": "acme", "location": " dijon "}
    assert dedup_key(a) == dedup_key(b)

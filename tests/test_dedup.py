from app.services.collector import dedup_key

def test_same_url_has_same_key():
    a = {"source_url": "https://example.com/job/1"}
    b = {"source_url": "https://example.com/job/1/"}
    assert dedup_key(a) == dedup_key(b)

import os
os.environ["DATABASE_URL"] = "sqlite:///./test_jobradar.db"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["COLLECTION_SOURCES"] = ""
os.environ["JOBRADAR_INTERNAL_KEY"] = "test-internal-key"

import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.database import Base, engine
    from app.main import app
    from app import models  # noqa: F401
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as test_client:
        yield test_client

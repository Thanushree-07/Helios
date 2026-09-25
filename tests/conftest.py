import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


@pytest.fixture(autouse=True)
def set_test_api_key(monkeypatch):
    """Every test automatically uses a known, fixed API key."""
    monkeypatch.setattr(settings, "api_key", "test-key-123")


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)
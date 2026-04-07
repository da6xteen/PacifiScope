import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from main import app

@pytest.fixture
def client():
    app.state.db = AsyncMock()
    app.state.redis = AsyncMock()
    with TestClient(app) as c:
        yield c

from fastapi.testclient import TestClient
import jwt
import pytest

from app.config.settings import settings
from app.main import app

client = TestClient(app)


def test_infrastructure_endpoint_unauthenticated():
    res = client.get("/api/v1/infrastructure")
    assert res.status_code == 401


def test_infrastructure_endpoint_authenticated():
    token = jwt.encode(
        {"sub": "infra_observer"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/infrastructure", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "operational"
    assert "components" in data
    assert len(data["components"]) == 5

    component_names = {c["name"] for c in data["components"]}
    assert "Models" in component_names
    assert "Repository" in component_names
    assert "Deployment" in component_names
    assert "Memory" in component_names
    assert "Storage" in component_names

    # Check some details
    models_comp = next(c for c in data["components"] if c["name"] == "Models")
    assert "Capabilities & Routing" in models_comp["details"]
    assert "Endpoint URL" in models_comp["details"]

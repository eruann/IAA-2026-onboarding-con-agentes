import pytest
from fastapi.testclient import TestClient


def test_health_sin_base_responde_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.db
def test_health_db_con_pgvector_instalado_responde_ok(client: TestClient) -> None:
    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json()["pgvector"]

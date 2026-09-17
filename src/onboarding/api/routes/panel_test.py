from fastapi.testclient import TestClient


def test_panel_renderiza_vacio(client: TestClient) -> None:
    response = client.get("/panel")

    assert response.status_code == 200
    assert "Panel del jefe" in response.text

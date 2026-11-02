from fastapi.testclient import TestClient

from onboarding.api.main import app, create_app


def test_la_interfaz_se_monta_en_ui_sin_romper_la_api() -> None:
    # La app del módulo es la que levanta uvicorn: la única con NiceGUI configurado.
    with TestClient(app) as client:
        ui_response = client.get("/ui/")
        health_response = client.get("/health")

    assert ui_response.status_code == 200
    assert "<title>Onboarding</title>" in ui_response.text
    assert health_response.status_code == 200


def test_crear_otra_app_no_reconfigura_la_interfaz() -> None:
    # NiceGUI es uno solo por proceso: crear otra app (como hacen los demás tests)
    # no tiene que fallar por intentar configurarlo de nuevo.
    other = create_app()

    assert other.url_path_for("health") == "/health"
    assert any(getattr(route, "path", "") == "/ui" for route in other.routes)

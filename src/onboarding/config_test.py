from onboarding.config import Settings


def test_url_de_proveedor_gestionado_se_convierte_a_psycopg() -> None:
    # Neon y Render entregan la URL sin driver explícito.
    settings = Settings(database_url="postgres://user:pass@host/db")

    assert settings.database_url.startswith("postgresql+psycopg://")


def test_url_con_driver_explicito_no_se_toca() -> None:
    url = "postgresql+psycopg://user:pass@host/db"

    assert Settings(database_url=url).database_url == url


def test_slack_deshabilitado_si_faltan_credenciales() -> None:
    assert not Settings(slack_bot_token=None, slack_signing_secret=None).slack_enabled

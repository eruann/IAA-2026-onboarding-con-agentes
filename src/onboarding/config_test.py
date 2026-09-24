import pytest

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


@pytest.mark.parametrize("vacio", ["", "   "])
def test_secretos_vacios_cuentan_como_no_configurados(vacio: str) -> None:
    # Render, Docker y .env dejan las variables sin valor como "" o espacios.
    settings = Settings(
        openrouter_api_key=vacio,
        slack_bot_token=vacio,
        slack_signing_secret=vacio,
    )

    assert settings.openrouter_api_key is None
    assert settings.slack_bot_token is None
    assert settings.slack_signing_secret is None


def test_slack_deshabilitado_si_los_tokens_estan_vacios() -> None:
    assert not Settings(slack_bot_token="", slack_signing_secret="").slack_enabled


def test_slack_habilitado_con_ambos_tokens() -> None:
    assert Settings(slack_bot_token="xoxb-test", slack_signing_secret="secreto").slack_enabled

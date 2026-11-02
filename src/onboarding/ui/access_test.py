from onboarding.config import Settings
from onboarding.ui.access import check_password, has_test_access, workshops_key, workshops_mode


def _settings(env: str, password: str | None = None) -> Settings:
    return Settings(env=env, admin_password=password)


def test_en_dev_se_entra_directo() -> None:
    assert workshops_mode(_settings("dev")) == "open"
    assert has_test_access(_settings("dev"), {})


def test_en_prod_sin_clave_los_talleres_quedan_desactivados() -> None:
    settings = _settings("prod", "")  # vacía en Render cuenta como no configurada
    assert workshops_mode(settings) == "off"
    assert not has_test_access(settings, {"test_key": workshops_key("")})


def test_en_prod_con_clave_hay_que_acertarla() -> None:
    settings = _settings("prod", "secreta")

    assert workshops_mode(settings) == "password"
    assert check_password(settings, "secreta") and not check_password(settings, "otra")
    assert has_test_access(settings, {"test_key": workshops_key("secreta")})
    assert not has_test_access(settings, {"test_key": workshops_key("otra")})
    assert not has_test_access(settings, {})

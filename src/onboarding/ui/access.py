# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Quién entra a los talleres (botón Test de la entrada).

- En dev (`ENV=dev`, lo de cada uno en su compu): se entra directo.
- En prod (la demo en Render): solo si está `ADMIN_PASSWORD`, y pidiéndola. Sin
  clave, los talleres quedan desactivados.

Al acertar la clave, el navegador guarda una huella de ella (no la clave): así no
hay que escribirla en cada visita y nadie entra copiando un valor sin conocerla.
"""

import hashlib
from typing import Literal

from onboarding.config import Settings

WorkshopsMode = Literal["open", "password", "off"]


def workshops_mode(settings: Settings) -> WorkshopsMode:
    if settings.env == "dev":
        return "open"
    return "password" if settings.admin_password else "off"


def workshops_key(password: str) -> str:
    """La huella que se guarda en el navegador al acertar la clave."""
    return hashlib.sha256(f"onboarding-talleres:{password}".encode()).hexdigest()


def check_password(settings: Settings, password: str) -> bool:
    secret = settings.admin_password
    return bool(secret) and password == secret.get_secret_value()


def has_test_access(settings: Settings, prefs: dict) -> bool:
    mode = workshops_mode(settings)
    if mode == "open":
        return True
    if mode == "off":
        return False
    return prefs.get("test_key") == workshops_key(settings.admin_password.get_secret_value())

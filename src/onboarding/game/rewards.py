# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Catálogo de canje. Titular: rol Experiencia.

Alcance del TP: catálogo ficticio (data/rewards.yaml). La integración real con
un vendedor de beneficios (Bonda, Betterfly) se diseña pero no se conecta. Las
firmas son una propuesta: se pueden cambiar al implementarlas.
"""


def list_rewards() -> list[dict]:
    """El catálogo de data/rewards.yaml."""
    raise NotImplementedError("TODO(experiencia): leer el catálogo")


def redeem(person_key: str, reward_key: str) -> int:
    """Canjea un premio: descuenta sus puntos (sin quedar en negativo) y devuelve los
    puntos que le quedan a la persona."""
    raise NotImplementedError("TODO(experiencia): canjear y guardar en redemptions")


def redemption_history(person_key: str) -> list[dict]:
    """Lo que canjeó una persona, del más nuevo al más viejo."""
    raise NotImplementedError("TODO(experiencia): historial de redemptions")

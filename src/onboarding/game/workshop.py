# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol Experiencia: interfaz y game design.

Solo declara: el chat con `validate_evidence`, las pruebas (las revisiones están en
`checks.py`) y el panel del jefe adentro del taller.
"""

from pathlib import Path

from onboarding.game.checks import review_quests, review_rewards
from onboarding.game.points import level_for
from onboarding.game.rewards import list_rewards, redeem
from onboarding.workshop import Embed, Tool, Workshop

# recorrido: taller-experiencia
WORKSHOP = Workshop(
    role="Experiencia",
    intent="validate_evidence",
    summary=(
        "Interfaz y game design: misiones, puntos, canje, el panel del jefe y Slack. "
        "Chateá con el agente que revisa evidencias, mirá el panel y revisá los datos "
        "del juego."
    ),
    tools=(
        Tool(level_for, "Calcular el nivel", "Escribí una cantidad de puntos."),
        Tool(
            review_quests,
            "Revisar las misiones",
            "Lee data/quests.yaml y marca lo que no cierra.",
        ),
        Tool(list_rewards, "Ver el catálogo de canje", "Pendiente hasta que exista el canje."),
        Tool(redeem, "Canjear un premio", "La key de una persona y la de un premio."),
        Tool(
            review_rewards,
            "Revisar el catálogo de canje",
            "Lee data/rewards.yaml y lo compara con los puntos de las misiones.",
        ),
    ),
    guide=Path(__file__).parent / "LEEME.md",
    embeds=(
        Embed(
            "Panel del jefe",
            "/panel",
            "Lo que ve el jefe: ingresantes y misiones pendientes, con los datos de tu "
            "base. Si está vacío, cargá la empresa ficticia con el seed (ver la guía).",
        ),
    ),
)

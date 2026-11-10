# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol Experiencia: interfaz y game design.

Solo declara: el chat con `validate_evidence`, su agente, las pruebas y el panel del
jefe adentro del taller. El juego (misiones, puntos, canje) es producto y queda en
game/: acá solo se llama.
"""

from pathlib import Path

# 1. Pruebas ad hoc (andamiaje): checks.py de este agente
from onboarding.agents.validate_evidence.checks import review_quests, review_rewards

# 2. Del agente (producto): node.py de este agente
# (ninguna)
# 3. Del código común (producto): knowledge layer, game y demás interfaces
from onboarding.game import level_for, list_rewards, redemption_history
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
        Tool(list_rewards, "Ver el catálogo de canje", "Muestra premios y puntos necesarios."),
        Tool(
            redemption_history,
            "Ver lo que canjeó una persona",
            "La key de una persona (ej.: ana-ingresante).",
        ),
        Tool(
            review_rewards,
            "Revisar el catálogo de canje",
            "Lee data/rewards.yaml y lo compara con los puntos de las misiones.",
        ),
    ),
    guide=Path(__file__).parent / "LEEME.md",
    greeting=(
        "Contame qué misión hiciste y qué evidencia tenés (qué hiciste, con quién, qué "
        "lo prueba), y te digo si alcanza para darla por cumplida."
    ),
    embeds=(
        Embed(
            "Panel del jefe",
            "/panel",
            "Lo que ve el jefe: ingresantes y misiones pendientes, con los datos de tu "
            "base. Si está vacío, cargá la empresa ficticia con el seed (ver la guía).",
        ),
    ),
)

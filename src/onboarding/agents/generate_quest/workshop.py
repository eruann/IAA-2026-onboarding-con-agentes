# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol Diseñador de misiones.

Solo declara: el chat con `generate_quest`, la revisión de propuestas (en
`checks.py`), las misiones actuales y lo que el agente usa de otros roles
(`retrieve` y `who_knows_about`).
"""

from pathlib import Path

from onboarding.agents.generate_quest.checks import review_proposal
from onboarding.game import review_quests
from onboarding.knowledge import retrieve, who_knows_about
from onboarding.workshop import Tool, Workshop

# recorrido: taller-misiones
WORKSHOP = Workshop(
    role="Diseñador de misiones",
    intent="generate_quest",
    summary=(
        "Misiones nuevas para cada puesto, a partir de su documentación y de quién sabe "
        "qué. Chateá con el agente que las propone y revisá sus propuestas antes de "
        "pasárselas a Experiencia y PM."
    ),
    tools=(
        Tool(
            review_proposal,
            "Revisar una misión propuesta",
            "Pegá lo que propuso el agente, en el formato de data/quests.yaml.",
        ),
        Tool(review_quests, "Ver las misiones actuales", "Para no proponer algo que ya existe."),
        Tool(
            retrieve,
            "Buscar documentación del puesto",
            "Lo que va a encontrar tu agente en la documentación (es de RAG).",
        ),
        Tool(
            who_knows_about,
            "¿Quién sabe de?",
            "A quién podría involucrar una misión (es de Grafo).",
        ),
    ),
    guide=Path(__file__).parent / "LEEME.md",
)

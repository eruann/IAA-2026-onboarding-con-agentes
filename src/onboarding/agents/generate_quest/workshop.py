# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol Diseñador de misiones.

Declara las pruebas: revisar una misión propuesta con las mismas reglas que usa
Experiencia, ver las misiones que ya existen y probar lo que usa el agente de
otros roles (`retrieve` y `who_knows_about`). Cómo propone misiones el agente está
en `node.py` y en su prompt, `agents/prompts/generate_quest.md`.
"""

import re
from pathlib import Path

import yaml

from onboarding.game import quest_table, quests_in_data, review_quests
from onboarding.knowledge import retrieve, who_knows_about
from onboarding.workshop import Tool, Workshop

# Un bloque ```yaml ... ``` como los que suelen devolver los modelos
_FENCE = re.compile(r"```(?:ya?ml)?\s*\n(.*?)```", re.DOTALL)


def review_proposal(proposal: str) -> str:
    """Revisa misiones propuestas, en el formato de data/quests.yaml, con las mismas
    reglas que las misiones del juego. Una key que ya existe cuenta como repetida."""
    block = _FENCE.search(proposal)
    try:
        data = yaml.safe_load(block.group(1) if block else proposal)
    except yaml.YAMLError as error:
        raise ValueError(f"No es YAML válido: {error}") from None
    quests = [data] if isinstance(data, dict) else data
    if not isinstance(quests, list) or not all(isinstance(quest, dict) for quest in quests):
        raise ValueError(
            "Tiene que ser una misión o una lista de misiones con el formato de "
            "data/quests.yaml (key, title, description, points, approver, evidence_required)."
        )
    existing = {quest.get("key") for quest in quests_in_data()}
    table, with_problems = quest_table(quests, seen=existing)
    verdict = (
        "✅ Lista para que la revisen Experiencia y PM."
        if not with_problems
        else f"**{with_problems}** de {len(quests)} con algo para corregir."
    )
    return f"{verdict}\n\n{table}"


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

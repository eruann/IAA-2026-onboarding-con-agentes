# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Pruebas ad hoc del taller del Diseñador de misiones: revisar lo que propone el agente
con las mismas reglas que las misiones del juego (`game.check_quests`)."""

import re

import yaml

from onboarding.game import REVIEW_COLUMNS, quests_in_data, review_rows
from onboarding.workshop import markdown_table

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
    rows = review_rows(quests, existing)
    with_problems = sum(row[-1] != "✅" for row in rows)
    verdict = (
        "✅ Lista para que la revisen Experiencia y PM."
        if not with_problems
        else f"**{with_problems}** de {len(quests)} con algo para corregir."
    )
    return f"{verdict}\n\n{markdown_table(REVIEW_COLUMNS, rows)}"

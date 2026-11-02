# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Misiones, puntos, canje y tono. Titular: rol Experiencia."""

from onboarding.game.quests import Quest, QuestStatus
from onboarding.game.tone import Tone

# Del taller: el Diseñador de misiones revisa sus propuestas con las mismas reglas
from onboarding.game.workshop import WORKSHOP, quest_table, quests_in_data, review_quests

# recorrido: juego-interfaz
__all__ = [
    "WORKSHOP",
    "Quest",
    "QuestStatus",
    "Tone",
    "quest_table",
    "quests_in_data",
    "review_quests",
]

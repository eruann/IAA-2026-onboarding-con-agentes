# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Misiones, puntos, canje y tono. Titular: rol Experiencia."""

# Del taller de Experiencia: el del Diseñador de misiones muestra lo mismo
from onboarding.game.board import (
    EmployeeBoard,
    ManagerBoard,
    MissionCard,
    PendingMission,
    employee_board,
    manager_board,
)
from onboarding.game.checks import quest_rows, review_quests
from onboarding.game.data import sync_game_data
from onboarding.game.people import PersonCard, list_people
from onboarding.game.quests import (
    STATUS_LABELS,
    Quest,
    QuestStatus,
    check_quests,
    quests_in_data,
)
from onboarding.game.rewards import list_rewards, redeem, redemption_history
from onboarding.game.tone import Tone
from onboarding.game.workshop import WORKSHOP

# Talleres de los roles de este paquete, para la interfaz (ver onboarding/workshop.py)
WORKSHOPS = (WORKSHOP,)

# recorrido: juego-interfaz
__all__ = [
    "STATUS_LABELS",
    "WORKSHOPS",
    "EmployeeBoard",
    "ManagerBoard",
    "MissionCard",
    "PendingMission",
    "PersonCard",
    "Quest",
    "QuestStatus",
    "Tone",
    "check_quests",
    "employee_board",
    "list_people",
    "list_rewards",
    "manager_board",
    "quest_rows",
    "quests_in_data",
    "redeem",
    "redemption_history",
    "review_quests",
    "sync_game_data",
]

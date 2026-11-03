# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Las misiones: su forma, sus estados y las reglas que tiene que cumplir cada una."""

import dataclasses
from dataclasses import dataclass
from typing import Literal, get_args

from onboarding.paths import load_data_yaml

QuestStatus = Literal["pending", "submitted", "approved", "rejected"]
Approver = Literal["manager", "helpdesk", "agent"]

# Cómo se nombra cada estado en pantalla (panel del jefe, tablero del empleado)
STATUS_LABELS: dict[str, str] = {
    "pending": "Pendiente",
    "submitted": "Esperando aprobación",
    "approved": "Aprobada",
    "rejected": "Rechazada",
}
# Alcance del TP
MIN_QUESTS, MAX_QUESTS = 6, 8


@dataclass(frozen=True)
# recorrido: mision
class Quest:
    key: str
    title: str
    description: str
    points: int
    approver: Approver
    evidence_required: str


QUEST_FIELDS = tuple(field.name for field in dataclasses.fields(Quest))
APPROVERS = get_args(Approver)


# TODO(experiencia + pm): llegar a las 6-8 misiones del TP en data/quests.yaml.
def quests_in_data() -> list[dict]:
    """Las misiones de data/quests.yaml, tal cual están escritas."""
    return load_data_yaml("quests.yaml", required=True)


def is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def field_problems(item: dict, fields: tuple[str, ...], seen: set) -> list[str]:
    """Campos que faltan o sobran, y `key` repetida (`seen` junta las ya vistas)."""
    problems = [f"falta {name}" for name in fields if item.get(name) in (None, "")]
    problems += [f"{name} no se usa" for name in item if name not in fields]
    if item.get("key") in seen:
        problems.append("key repetida")
    seen.add(item.get("key"))
    return problems


def check_quests(quests: list[dict], existing_keys: set | None = None) -> list[list[str]]:
    """Lo que no cierra de cada misión, en el mismo orden. `existing_keys`: las que ya
    existen en el juego (una propuesta con esa key cuenta como repetida)."""
    seen = set(existing_keys or ())
    result = []
    for quest in quests:
        problems = field_problems(quest, QUEST_FIELDS, seen)
        if "points" in quest and not is_positive_int(quest["points"]):
            problems.append("points tiene que ser un entero mayor que cero")
        if quest.get("approver") and quest["approver"] not in APPROVERS:
            problems.append(f"approver tiene que ser {', '.join(APPROVERS)}")
        result.append(problems)
    return result


# Las columnas de la revisión de misiones (la muestran los talleres de Experiencia y
# del Diseñador de misiones)
REVIEW_COLUMNS = ("key", "título", "puntos", "aprueba", "revisión")


def review_rows(quests: list[dict], existing_keys: set | None = None) -> list[tuple]:
    """Una fila por misión, en el orden de REVIEW_COLUMNS, con lo que no cierra de
    cada una (o ✅ si está bien)."""
    problems = check_quests(quests, existing_keys)
    return [
        (
            quest.get("key", "—"),
            quest.get("title", "—"),
            quest.get("points", "—"),
            quest.get("approver", "—"),
            "; ".join(found) or "✅",
        )
        for quest, found in zip(quests, problems, strict=True)
    ]

# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Pruebas ad hoc del taller de Experiencia: leen los YAML del juego y muestran lo
que no cierra, con las reglas de `game/quests.py` (producto). No cambian nada."""

from onboarding.game import (
    MAX_QUESTS,
    MIN_QUESTS,
    REVIEW_COLUMNS,
    field_problems,
    is_positive_int,
    quests_in_data,
    review_rows,
)
from onboarding.paths import load_data_yaml
from onboarding.workshop import markdown_table

REWARD_FIELDS = ("key", "title", "cost")


def _total_points(quests: list[dict]) -> int:
    return sum(quest["points"] for quest in quests if is_positive_int(quest.get("points")))


def review_quests() -> str:
    """Las misiones de data/quests.yaml en una tabla, con lo que no cierra."""
    quests = quests_in_data()
    rows = review_rows(quests)
    with_problems = sum(row[-1] != "✅" for row in rows)
    if MIN_QUESTS <= len(quests) <= MAX_QUESTS:
        count = f"✅ {len(quests)} misiones (el alcance pide de {MIN_QUESTS} a {MAX_QUESTS})."
    else:
        count = f"⚠️ Hay {len(quests)} misiones: el alcance pide de {MIN_QUESTS} a {MAX_QUESTS}."
    summary = (
        f"**{with_problems}** con algo para revisar · **{_total_points(quests)}** puntos en total."
    )
    return "\n\n".join([count, summary, markdown_table(REVIEW_COLUMNS, rows)])


def review_rewards() -> str:
    """El catálogo de data/rewards.yaml, comparado con los puntos de todas las misiones."""
    rewards = load_data_yaml("rewards.yaml", required=True)
    total = _total_points(quests_in_data())
    rows = []
    seen: set = set()
    for reward in rewards:
        problems = field_problems(reward, REWARD_FIELDS, seen)
        cost = reward.get("cost")
        share = "—"
        if "cost" in reward and not is_positive_int(cost):
            problems.append("cost tiene que ser un entero mayor que cero")
        elif total and cost:
            share = f"{cost / total:.0%}"
            if cost > total:
                problems.append("cuesta más que todas las misiones juntas")
        rows.append(
            (
                reward.get("key", "—"),
                reward.get("title", "—"),
                cost if cost is not None else "—",
                share,
                "; ".join(problems) or "✅",
            )
        )
    table = markdown_table(
        ("key", "premio", "costo", "de lo que se puede juntar", "revisión"), rows
    )
    return (
        f"Todas las misiones juntas dan **{total}** puntos. La columna *de lo que se "
        f"puede juntar* dice qué parte de eso cuesta cada premio.\n\n{table}"
    )

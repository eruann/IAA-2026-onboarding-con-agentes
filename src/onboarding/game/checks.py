# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Revisiones del taller de Experiencia: leen los YAML del juego y muestran lo que
no cierra, con las reglas de `game/quests.py`. No cambian nada."""

from onboarding.game.quests import (
    MAX_QUESTS,
    MIN_QUESTS,
    check_quests,
    field_problems,
    is_positive_int,
    quests_in_data,
)
from onboarding.paths import load_data_yaml
from onboarding.workshop import markdown_table

REWARD_FIELDS = ("key", "title", "cost")


def quest_rows(quests: list[dict], existing_keys: set | None = None) -> tuple[str, int]:
    """Las misiones en una tabla, con lo que no cierra de cada una, y cuántas tienen
    algo para revisar. La usan este taller y el del Diseñador de misiones."""
    problems = check_quests(quests, existing_keys)
    table = markdown_table(
        ("key", "título", "puntos", "aprueba", "revisión"),
        (
            (
                quest.get("key", "—"),
                quest.get("title", "—"),
                quest.get("points", "—"),
                quest.get("approver", "—"),
                "; ".join(found) or "✅",
            )
            for quest, found in zip(quests, problems, strict=True)
        ),
    )
    return table, sum(bool(found) for found in problems)


def _total_points(quests: list[dict]) -> int:
    return sum(quest["points"] for quest in quests if is_positive_int(quest.get("points")))


def review_quests() -> str:
    """Las misiones de data/quests.yaml en una tabla, con lo que no cierra."""
    quests = quests_in_data()
    table, with_problems = quest_rows(quests)
    if MIN_QUESTS <= len(quests) <= MAX_QUESTS:
        count = f"✅ {len(quests)} misiones (el alcance pide de {MIN_QUESTS} a {MAX_QUESTS})."
    else:
        count = f"⚠️ Hay {len(quests)} misiones: el alcance pide de {MIN_QUESTS} a {MAX_QUESTS}."
    summary = (
        f"**{with_problems}** con algo para revisar · **{_total_points(quests)}** puntos en total."
    )
    return "\n\n".join([count, summary, table])


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

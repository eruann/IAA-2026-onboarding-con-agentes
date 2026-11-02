# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol Experiencia: interfaz y game design.

Declara las pruebas, suma dos revisiones de los datos del juego (`review_quests` y
`review_rewards`, que leen los YAML sin cambiarlos) y muestra el panel del jefe
adentro del taller. Cómo se cargan las misiones o cómo funciona el canje está en
`game/`, `api/` y `bot/`.
"""

import dataclasses
import typing
from pathlib import Path

import yaml

from onboarding.game.points import level_for
from onboarding.game.quests import Approver, Quest
from onboarding.workshop import Embed, Tool, Workshop, markdown_row

# data/ está en la raíz del repo, tanto local como en Docker (/app/data)
DATA_DIR = Path(__file__).resolve().parents[3] / "data"
# Alcance del TP (ver data/quests.yaml)
MIN_QUESTS, MAX_QUESTS = 6, 8
QUEST_FIELDS = tuple(field.name for field in dataclasses.fields(Quest))
REWARD_FIELDS = ("key", "title", "cost")
APPROVERS = typing.get_args(Approver)


def _load(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"No está {path}.")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def _problems(item: dict, fields: tuple[str, ...], seen: set) -> list[str]:
    """Problemas comunes a misiones y premios: campos que faltan o sobran y claves repetidas."""
    problems = [f"falta {name}" for name in fields if item.get(name) in (None, "")]
    problems += [f"{name} no se usa" for name in item if name not in fields]
    if item.get("key") in seen:
        problems.append("key repetida")
    seen.add(item.get("key"))
    return problems


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def review_quests() -> str:
    """Las misiones de data/quests.yaml en una tabla, con lo que no cierra."""
    quests = _load("quests.yaml")
    rows = []
    seen: set = set()
    with_problems = 0
    for quest in quests:
        problems = _problems(quest, QUEST_FIELDS, seen)
        if "points" in quest and not _is_positive_int(quest["points"]):
            problems.append("points tiene que ser un entero mayor que cero")
        if quest.get("approver") and quest["approver"] not in APPROVERS:
            problems.append(f"approver tiene que ser {', '.join(APPROVERS)}")
        with_problems += bool(problems)
        rows.append(
            markdown_row(
                (
                    quest.get("key", "—"),
                    quest.get("title", "—"),
                    quest.get("points", "—"),
                    quest.get("approver", "—"),
                    "; ".join(problems) or "✅",
                )
            )
        )

    total = sum(q["points"] for q in quests if _is_positive_int(q.get("points")))
    if MIN_QUESTS <= len(quests) <= MAX_QUESTS:
        count = f"✅ {len(quests)} misiones (el alcance pide de {MIN_QUESTS} a {MAX_QUESTS})."
    else:
        count = f"⚠️ Hay {len(quests)} misiones: el alcance pide de {MIN_QUESTS} a {MAX_QUESTS}."
    return "\n".join(
        [
            count,
            "",
            f"**{with_problems}** con algo para revisar · **{total}** puntos en total.",
            "",
            "| key | título | puntos | aprueba | revisión |",
            "|---|---|---|---|---|",
            *rows,
        ]
    )


def review_rewards() -> str:
    """El catálogo de data/rewards.yaml, comparado con los puntos de todas las misiones."""
    rewards = _load("rewards.yaml")
    quests = _load("quests.yaml")
    total = sum(q["points"] for q in quests if _is_positive_int(q.get("points")))
    rows = []
    seen: set = set()
    for reward in rewards:
        problems = _problems(reward, REWARD_FIELDS, seen)
        cost = reward.get("cost")
        if "cost" in reward and not _is_positive_int(cost):
            problems.append("cost tiene que ser un entero mayor que cero")
            share = "—"
        else:
            share = f"{cost / total:.0%}" if total and cost else "—"
            if total and cost and cost > total:
                problems.append("cuesta más que todas las misiones juntas")
        rows.append(
            markdown_row(
                (
                    reward.get("key", "—"),
                    reward.get("title", "—"),
                    cost if cost is not None else "—",
                    share,
                    "; ".join(problems) or "✅",
                )
            )
        )
    return "\n".join(
        [
            f"Todas las misiones juntas dan **{total}** puntos. La columna *de lo que se "
            "puede juntar* dice qué parte de eso cuesta cada premio.",
            "",
            "| key | premio | costo | de lo que se puede juntar | revisión |",
            "|---|---|---|---|---|",
            *rows,
        ]
    )


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

# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Pruebas ad hoc del taller de Grafo: funciones armadas solo para probar o medir en
el taller, que no son parte del producto.

Hoy, autorizar lo pendiente del grafo con una tarjeta: `authorize` aprueba o
rechaza uno o varios, guarda la organización que se escriba y siempre muestra lo que
queda pendiente (`pending`, con «falta» si a la persona le falta la organización). La lógica es del
producto (`pending_reviews`, `review` y `set_organization`, en la knowledge layer);
acá solo se la pone en el taller.

Y ver el grafo: una página interactiva (`graph_page.py`, en `GRAPH_PAGE`) que el
taller muestra embebida. Importarla desde acá la registra.

Una nueva va acá, con su test en `checks_test.py`, y se suma en la sección 1 de
`workshop.py` (por ejemplo, medir la cobertura contra
eval/informal_network_ground_truth.yaml).
"""

import re
from dataclasses import dataclass
from typing import Literal

from onboarding.agents.extract_knowledge.graph_page import GRAPH_PAGE as GRAPH_PAGE
from onboarding.knowledge import (
    Review,
    pending_reviews,
    person_profile,
    review,
    set_organization,
)

KINDS = {"relation": "Relación", "same_person": "¿Misma persona?", "conflict": "Contradicción"}
CRITICALITIES = {"high": "alta", "medium": "media", "low": "baja", "": ""}
MISSING = "falta"


@dataclass(frozen=True)
class PendingRow:
    """Una fila de la tabla: lo que espera revisión, con su id para autorizarlo."""

    edge_id: int
    kind: str
    summary: str
    evidence: str
    criticality: str
    detail: str
    # La de la persona; "falta" si no se sabe (ni organigrama, ni frase, ni su nodo).
    # Vacía en las dudas de identidad, que son dos personas
    organization: str


def pending() -> list[PendingRow]:
    """Lo que espera revisión: relaciones, dudas de identidad y contradicciones."""
    return [
        PendingRow(
            r.edge_id,
            KINDS[r.kind],
            r.summary,
            r.evidence,
            CRITICALITIES.get(r.criticality, r.criticality),
            r.detail,
            _organization(r),
        )
        for r in pending_reviews()
    ]


def authorize(
    decision: Literal["aprobar", "rechazar"], edge_ids: str = "", organization: str = ""
) -> str:
    """Aprueba o rechaza lo pendiente con esos ids ("3" o "3, 5, 7") y muestra lo que
    queda pendiente. Sin ids, solo muestra la lista: así se eligen. Si escribís la
    organización, se guarda en la persona de esas relaciones a la que le falta,
    aunque la relación se rechace."""
    ids = [int(found) for found in re.findall(r"\d+", edge_ids)]
    done = _decide(ids, decision, organization) if ids else ""
    return "\n\n".join(part for part in (done, _table(pending())) if part)


def _decide(ids: list[int], decision: str, organization: str) -> str:
    # La organización, antes de decidir: después ya no están en la lista de pendientes
    saved = 0
    if organization.strip():
        people = {r.person_id for r in pending_reviews() if r.edge_id in ids and r.person_id}
        missing = sorted(pid for pid in people if not _organization_of(pid))
        saved = sum(set_organization(pid, organization) for pid in missing)
    said = []
    for edge_id in ids:
        try:
            said.append(review(edge_id, approve=decision == "aprobar"))
        except ValueError as error:  # uno ya revisado o inexistente no frena a los demás
            said.append(str(error))
    if saved:
        said.append(f"Guardé la organización de {saved} persona{'s' if saved > 1 else ''}.")
    return "**" + " ".join(said) + "**"


def _table(rows: list[PendingRow]) -> str:
    """La lista de pendientes como tabla (la tarjeta muestra el texto como markdown)."""
    if not rows:
        return "No hay nada pendiente de revisar."

    def cell(text: object) -> str:
        return str(text).replace("|", "\\|").replace("\n", " ")

    lines = [
        "Pendientes (usá el `edge_id`):",
        "",
        "| edge_id | tipo | qué dice | frase | criticidad | detalle | organización |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        values = (
            r.edge_id,
            r.kind,
            r.summary,
            f"«{r.evidence}»",
            r.criticality,
            r.detail,
            r.organization,
        )
        lines.append("| " + " | ".join(cell(v) for v in values) + " |")
    return "\n".join(lines)


def _organization(r: Review) -> str:
    if r.kind == "same_person":
        return ""
    return r.organization or _organization_of(r.person_id) or MISSING


def _organization_of(person_id: str) -> str:
    # La del nodo o, si es de la empresa, la del organigrama
    return person_profile(person_id, person_id).organization

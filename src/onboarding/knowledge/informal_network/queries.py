# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Consultas al grafo. Es lo que alimenta las misiones y las derivaciones.

Primero se busca por palabras, sin modelo. Si no aparece nada, el modelo elige
los temas del grafo más cercanos a la consulta ("IVA" -> "impuestos"). Con un
modelo, además, ordena a las personas por quién encaja mejor con la pregunta.
"""

import re
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Literal, overload

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from onboarding.knowledge.informal_network.store import CONFIRMED, REJECTED, _key, load_graph
from onboarding.llm import get_structured_model, load_prompt
from onboarding.paths import CORPUS_DIR

RELATED_PROMPT = Path(__file__).with_name("related_prompt.md")
RANK_PROMPT = Path(__file__).with_name("rank_prompt.md")
ORG_CHART = "organigrama.md"

# Cómo nombra el organigrama a cada persona: "Martín Ibarra es el Gerente General y
# reporta a...", "Silvina Ortega lleva Compras y Administración" o, en una lista,
# "Reportan a Ignacio: Rocío Miranda, Jefa de Control de Calidad y Validaciones; ...".
# El puesto termina en una coma, un punto y coma, un " y reporta" (una "y" seguida de
# minúscula) o el fin de la oración ("Analista de QA Sr. y padrino" no corta en "Sr.").
_NAME = r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+ [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"
_ROLE = r"(?P<role>.+?)(?=,|;| y [a-záéíóúñ]|\.(?:\s+[A-ZÁÉÍÓÚÑ]|\s*$))"
_SAYS_ROLE = re.compile(rf"(?P<name>{_NAME}) (?P<verb>es (?:el |la )?|lleva ){_ROLE}", re.M)
_LISTED_ROLE = re.compile(rf"(?:: |; (?:y )?)(?P<name>{_NAME}), {_ROLE}", re.M)
_COMPANY = re.compile(r"^(?P<company>[^\n#]+?) tiene \w+ áreas", re.M)

# Las relaciones que dicen que una persona sabe de algo: de un tema o de un proceso
_KNOWLEDGE = {"knows_about", "owns_process"}
# Conectores y las palabras de la pregunta misma ("¿quién es el que más sabe de...?")
_STOPWORDS = set(
    "de del la el los las en con para por sobre y a un una "
    "quien quienes que es mas sabe saben conoce cual como se".split()
)


@dataclass(frozen=True)
class Fact:
    """Lo que se sabe y no está escrito: quién, de qué, y la frase que lo dijo."""

    person: str
    relation: str
    about: str
    evidence: str
    confirmed: bool
    # True si no coincidió por palabras y `about` es un tema cercano que eligió el modelo
    nearby: bool = False
    # El id del nodo de la persona: dos homónimos tienen el mismo nombre y otro id
    person_id: str = ""
    # Por qué encaja con la pregunta, según el modelo que ordena; vacío sin modelo
    reason: str = ""


@dataclass(frozen=True)
class Expert:
    """A quién se deriva: la persona, su puesto y dónde trabaja, si se sabe."""

    name: str
    position: str  # vacío si no se sabe
    organization: str  # la empresa propia, una de afuera o vacío si no se sabe
    internal: bool  # está en el organigrama
    # Por qué se la deriva, según el modelo ("no figura como oficial de cuentas; se
    # acerca por su perfil comercial"). Vacío sin modelo
    reason: str = ""
    # Si las relaciones por las que se la deriva están aprobadas: "confirmada",
    # "pendiente" o "1 de 2 confirmadas". Vacío en `person_profile`, que no tiene relación
    status: str = ""


@lru_cache
def _org_chart() -> tuple[str, dict[str, tuple[str, str]]]:
    """El nombre de la empresa y, por persona del organigrama (con su clave sin
    tildes), su nombre como está escrito y su puesto."""
    text = (CORPUS_DIR / ORG_CHART).read_text(encoding="utf-8")
    company = _COMPANY.search(text)
    positions: dict[str, tuple[str, str]] = {}
    for match in [*_SAYS_ROLE.finditer(text), *_LISTED_ROLE.finditer(text)]:
        role = match["role"].strip()
        if match.groupdict().get("verb") == "lleva ":
            role = f"A cargo de {role}"
        # La primera vez que aparece es su puesto; después se la nombra de pasada
        positions.setdefault(_key(match["name"]), (match["name"], role))
    return (company["company"] if company else "la empresa"), positions


def person_profile(name: str, person_id: str = "") -> Expert:
    """Puesto y empresa de una persona: del organigrama si es de la empresa; si no,
    lo que dijo la conversación que la nombró (guardado en su nodo del grafo).

    Se busca por `person_id` si viene: "Diego Fernandez" del Banco Macro
    (`diego-fernandez-banco-macro`) no es el Diego Fernández del organigrama."""
    company, positions = _org_chart()
    key = _key(person_id or name)
    if key in positions:
        return Expert(name, positions[key][1], company, internal=True)
    node = next((n for n in load_graph()["nodes"] if n["id"] == key), {})
    attributes = node.get("attributes", {})
    return Expert(
        name, attributes.get("position", ""), attributes.get("organization", ""), internal=False
    )


def _words(text: str) -> set[str]:
    # Raíz simple para el plural: "impuestos" -> "impuesto", "redes" -> "rede" y "red"
    stems = set()
    for word in _key(text).split("-"):
        if word and word not in _STOPWORDS:
            stems.add(word.removesuffix("s"))
            if word.endswith("es") and len(word) > 4:
                stems.add(word[:-2])
    return stems


def _ranked_facts(topic: str) -> list[Fact]:
    """Las relaciones del grafo sobre el tema, de la persona con más respaldo a la de menos.

    Respaldo: primero cuántas relaciones confirmadas tiene la persona sobre el
    tema, después cuántas en total. Las pendientes van después de las confirmadas.
    """
    graph = load_graph()
    wanted = _words(topic)
    names = {n["id"]: n["name"] for n in graph["nodes"]}
    matching = {n["id"] for n in graph["nodes"] if wanted & _words(n["name"])}
    facts = [
        Fact(
            person=names[e["source"]],
            relation=e["relation"],
            about=names[e["target"]],
            evidence=e["evidence"],
            confirmed=e["status"] == CONFIRMED,
            person_id=e["source"],
        )
        for e in graph["edges"]
        if e["relation"] in _KNOWLEDGE and e["target"] in matching and e["status"] != REJECTED
    ]
    confirmed = {f.person: sum(g.confirmed for g in facts if g.person == f.person) for f in facts}
    total = {f.person: sum(g.person == f.person for g in facts) for f in facts}
    return sorted(
        facts, key=lambda f: (-confirmed[f.person], -total[f.person], f.person, not f.confirmed)
    )


def related_topics(question: str, model: BaseChatModel | None = None) -> list[str]:
    """Los temas del grafo más cercanos a la consulta, elegidos por el modelo.

    Solo devuelve nombres que están en el grafo: el modelo elige, no inventa.
    Con el grafo vacío no llama al modelo.
    """
    names = [n["name"] for n in load_graph()["nodes"] if n["type"] in {"topic", "process"}]
    if not names:
        return []
    # El enum restringe la salida a los temas que hay: no puede nombrar uno nuevo
    schema = {
        "title": "temas_cercanos",
        "description": "Temas del grafo cercanos a la consulta.",
        "type": "object",
        "properties": {"topics": {"type": "array", "items": {"type": "string", "enum": names}}},
        "required": ["topics"],
    }
    chooser = (model or get_structured_model()).with_structured_output(schema, method="json_schema")
    listed = "\n".join(f"- {name}" for name in names)
    output = chooser.invoke(
        [
            SystemMessage(f"{load_prompt(RELATED_PROMPT)}\n<temas>\n{listed}\n</temas>"),
            HumanMessage(question),
        ]
    )
    # Por si el proveedor no respeta el enum
    chosen = [t for t in (output or {}).get("topics", []) if t in names]
    return list(dict.fromkeys(chosen))[:3]


def what_is_known_about(
    topic: str, limit: int = 5, model: BaseChatModel | None = None
) -> list[Fact]:
    """El procedimiento no escrito: lo que se dijo de un tema, con quién lo sabe.

    Mismo orden que `who_knows_about`. Cada `Fact` trae la frase que lo respalda.
    Sin coincidencias por palabras, busca en los temas cercanos (`related_topics`).
    """
    facts = _ranked_facts(topic)
    if not facts:
        nearby = [f for name in related_topics(topic, model) for f in _ranked_facts(name)]
        facts = [replace(f, nearby=True) for f in dict.fromkeys(nearby)]
    if model is not None:
        facts = _rank_people(topic, facts, model)
    return facts[:limit]


def _rank_people(question: str, facts: list[Fact], model: BaseChatModel) -> list[Fact]:
    """Las personas de `facts`, de la que mejor encaja con la pregunta a la que peor,
    según el modelo. Las palabras solo encuentran candidatos: para "¿quién es el
    oficial de cuentas del banco?" encaja más alguien con perfil comercial con el
    banco que alguien de una tarea puntual, aunque los dos tengan "banco" en un tema.

    El modelo ve todo lo que se sabe de cada una, no solo lo que coincidió. Las que
    no nombra quedan afuera: que tengan "banco" en un tema no las hace el maestranza
    del banco. Si nadie encaja, no queda nadie. Se lo llama aunque haya una sola. Si
    la salida viene rota, queda el orden de antes, sin descartar a nadie.
    """
    ids = list(dict.fromkeys(f.person_id for f in facts))
    if not ids:
        return facts
    graph = load_graph()
    names = {n["id"]: n["name"] for n in graph["nodes"]}
    profiles = []
    for pid in ids:
        expert = person_profile(names.get(pid, pid), pid)
        details = ", ".join(p for p in (expert.position, expert.organization) if p)
        lines = [f"- {pid}: {expert.name}" + (f" ({details})" if details else "")]
        lines += [
            f"  - {e['relation']} {names.get(e['target'], e['target'])} («{e['evidence']}»)"
            for e in graph["edges"]
            if e["source"] == pid and e["relation"] in _KNOWLEDGE and e["status"] != REJECTED
        ]
        profiles.append("\n".join(lines))
    # El enum restringe la salida a los candidatos: no puede nombrar a otro
    schema = {
        "title": "quien_encaja",
        "description": "Personas, de la que mejor encaja a la que peor, con el motivo.",
        "type": "object",
        "properties": {
            "people": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "enum": ids},
                        "reason": {
                            "type": "string",
                            "description": "Por qué encaja; si la función no figura tal "
                            "cual en lo que se sabe, decilo.",
                        },
                    },
                    "required": ["id", "reason"],
                },
            }
        },
        "required": ["people"],
    }
    ranker = model.with_structured_output(schema, method="json_schema")
    listed = "\n".join(profiles)
    output = ranker.invoke(
        [
            SystemMessage(f"{load_prompt(RANK_PROMPT)}\n<personas>\n{listed}\n</personas>"),
            HumanMessage(question),
        ]
    )
    chosen = output.get("people") if isinstance(output, dict) else None
    if not isinstance(chosen, list):  # salida rota: mejor el orden por respaldo que nada
        return facts
    # Por si el proveedor no respeta el enum: un id inventado no cuenta. Cada uno viene
    # con su motivo; si viene el id solo, sin motivo
    reasons: dict[str, str] = {}
    for item in chosen:
        pid, reason = (item.get("id"), item.get("reason")) if isinstance(item, dict) else (item, "")
        if isinstance(pid, str) and pid in ids and pid not in reasons:
            reasons[pid] = reason if isinstance(reason, str) else ""
    order = list(reasons)
    return sorted(
        (replace(f, reason=reasons[f.person_id]) for f in facts if f.person_id in reasons),
        key=lambda f: order.index(f.person_id),
    )


# recorrido: quien-sabe
@overload
def who_knows_about(
    topic: str,
    limit: int = 3,
    model: BaseChatModel | None = None,
    detailed: Literal[False] = False,
) -> list[str]: ...
@overload
def who_knows_about(
    topic: str,
    limit: int = 3,
    model: BaseChatModel | None = None,
    *,
    detailed: Literal[True],
) -> list[Expert]: ...
def who_knows_about(
    topic: str,
    limit: int = 3,
    model: BaseChatModel | None = None,
    detailed: bool = False,
) -> list[str] | list[Expert]:
    """Personas que saben de un tema, de más a menos respaldo.

    Lo usa el agente cuando no hay soporte documental: en vez de inventar,
    responde "no tengo esta información, preguntale a X".

    Por defecto, solo los nombres: es lo acordado con los demás roles (RAG deriva
    con `people[0]`). Con `detailed=True`, la ficha de cada una (`Expert`): su
    puesto y su empresa si se saben (`person_profile`), por qué se la deriva y si
    sus relaciones están aprobadas. Los dos `@overload` de arriba simulan la
    sobrecarga: le dicen al editor qué devuelve en cada caso.
    """
    facts = what_is_known_about(topic, limit=1000, model=model)
    # Sin repetir, en orden; por id, para no juntar a dos homónimos
    people = {f.person_id: f for f in facts}
    experts = [
        replace(
            person_profile(f.person, pid),
            reason=f.reason,
            status=_status([g.confirmed for g in facts if g.person_id == pid]),
        )
        for pid, f in list(people.items())[:limit]
    ]
    return experts if detailed else [expert.name for expert in experts]


def _status(confirmed: list[bool]) -> str:
    """El estado de las relaciones por las que se deriva a alguien: "confirmada" si
    lo están todas, "pendiente" si ninguna, y si hay de las dos, cuántas."""
    if all(confirmed):
        return "confirmada"
    if not any(confirmed):
        return "pendiente"
    return f"{sum(confirmed)} de {len(confirmed)} confirmadas"

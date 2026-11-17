# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Las personas que ya se conocen y qué tan parecido es un nombre a otro.

Sirve para no duplicar a alguien: antes de guardar a "Diego Fernandez Lopez Monier"
conviene saber si es el "Diego Fernández" del organigrama. Acá está la parte sin
modelo (los candidatos y el parecido literal de los nombres); la parte semántica la
evalúa el agente con el modelo (agents/extract_knowledge/identity.py).
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Literal

from onboarding.knowledge.informal_network.queries import _org_chart
from onboarding.knowledge.informal_network.store import REJECTED, _key, load_graph

# Dos palabras cuentan como la misma con este parecido: "Gorosito" y "Gorosita"
SAME_WORD = 0.85
# Un nombre de una sola palabra ("Diego", "Gorosito") coincide con demasiada gente
SINGLE_WORD_CAP = 0.6


@dataclass(frozen=True)
class KnownPerson:
    """Alguien que ya está en el organigrama o en el grafo."""

    name: str
    position: str
    organization: str
    source: Literal["organigrama", "grafo"]
    # Lo que se sabe de la persona en el grafo: "sabe de X («frase»)"
    known: tuple[str, ...] = field(default=())
    # El id del nodo: con homónimos, el nombre no alcanza para saber quién es
    id: str = ""


def known_people() -> list[KnownPerson]:
    """El organigrama más las personas del grafo, sin repetir: si alguien está en los
    dos, gana el organigrama (su puesto es el oficial), con lo que dice el grafo."""
    company, positions = _org_chart()
    graph = load_graph()
    names = {n["id"]: n["name"] for n in graph["nodes"]}
    known: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        if edge["source"] in names and edge["target"] in names and edge["status"] != REJECTED:
            line = f"{edge['relation']} {names[edge['target']]} («{edge['evidence']}»)"
            known.setdefault(edge["source"], []).append(line)

    people: dict[str, KnownPerson] = {}
    for node in graph["nodes"]:
        if node["type"] != "person":
            continue
        attributes = node.get("attributes", {})
        people[node["id"]] = KnownPerson(
            node["name"],
            attributes.get("position", ""),
            attributes.get("organization", ""),
            "grafo",
            tuple(known.get(node["id"], [])),
            node["id"],
        )
    for person_id, (name, position) in positions.items():
        # El puesto es el oficial; el nombre, el más completo que se conozca
        in_graph = people[person_id].name if person_id in people else ""
        if len(in_graph.split()) > len(name.split()):
            name = in_graph
        people[person_id] = KnownPerson(
            name, position, company, "organigrama", tuple(known.get(person_id, [])), person_id
        )
    return list(people.values())


def same_name(a: str, b: str) -> bool:
    """El mismo nombre sin contar tildes, mayúsculas ni signos: "Julián Rearte" y
    "julian rearte". No alcanza con que uno esté contenido en el otro."""
    return bool(_key(a)) and _key(a) == _key(b)


def name_similarity(a: str, b: str) -> float:
    """Parecido literal entre dos nombres, de 0 a 1, sin modelo.

    Sin tildes ni mayúsculas. Cuenta cuántas palabras del nombre más corto están en
    el otro (con errores de tipeo: "Gorosita" vale por "Gorosito"), así un nombre
    con apellidos de más no pierde: "Diego Fernández" contra "Diego Fernandez Lopez
    Monier" da 1. Si el más corto tiene una sola palabra, como mucho 0,6.
    """
    words_a, words_b = _key(a).split("-"), _key(b).split("-")
    if not _key(a) or not _key(b):
        return 0.0
    shorter, longer = sorted((words_a, words_b), key=len)
    shared = sum(
        any(SequenceMatcher(None, word, other).ratio() >= SAME_WORD for other in longer)
        for word in shorter
    )
    coverage = shared / len(shorter)
    if len(shorter) == 1:
        coverage = min(coverage, SINGLE_WORD_CAP)
    # El nombre entero solo cuenta si es casi igual (un error de tipeo): "Julio Cesar"
    # y "Julián Rearte" se parecen como texto, pero no son el mismo nombre
    whole = SequenceMatcher(None, _key(a), _key(b)).ratio()
    return round(max(coverage, whole if whole >= SAME_WORD else 0.0), 2)

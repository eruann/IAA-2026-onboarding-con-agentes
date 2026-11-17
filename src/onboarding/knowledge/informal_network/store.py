# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Grafo de la red informal guardado en un JSON. Titular: rol Grafo cultural y datos.

Es provisorio: persiste lo que se extrae hasta que estén las tablas nodes/edges
(models.py). Usa los mismos nombres de campos para que la migración sea directa.

Al dar de alta una relación:
- si ya está, no se hace nada;
- si niega una que ya está, esa pasa a pendiente y guarda la frase en `history`;
- si choca con otra exclusiva ("es el único que..."), se guardan las dos en
  pendiente y un nodo `conflict` las une con aristas `contradicts`.

Aparte, `save_possible_match` une con una arista `may_be_same` a dos personas que
pueden ser la misma (la duda de agents/extract_knowledge/identity.py).

Lo pendiente lo revisa una persona: `pending_reviews` lo lista y `review` lo aprueba
o lo rechaza (una relación, una duda de identidad o una contradicción).
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

from onboarding.knowledge.informal_network.triples import KnowledgeTriple
from onboarding.paths import DATA_DIR

GRAPH_PATH = DATA_DIR / "informal_network.json"

PENDING = 0  # una persona tiene que confirmarla
CONFIRMED = 1
# Alguien la revisó y no vale: queda con su historial, pero las consultas no la ven y
# si se vuelve a decir no se propone de nuevo
REJECTED = 2

# Cómo se lee cada relación en una revisión
_RELATION_NAMES = {
    "knows_about": "sabe de",
    "introduced": "presentó a",
    "belongs_to": "pertenece a",
    "owns_process": "es responsable de",
    "works_with": "trabaja con",
}

# La extracción no dice de qué tipo es cada nodo: sale de la relación.
# El sujeto siempre es una persona.
_TARGET_TYPE = {
    "knows_about": "topic",
    "belongs_to": "area",
    "owns_process": "process",
    "introduced": "person",
    "works_with": "person",
}

# Las que valen en los dos sentidos: "A trabaja con B" es lo mismo que "B trabaja
# con A", así que la inversa no se guarda como otra relación
_SYMMETRIC = {"works_with"}

# Las que dicen que alguien hace algo o sabe de algo: si ese algo se hace con una
# herramienta (el atributo `tool` de su nodo), la persona sabe de la herramienta
_DOES = ("knows_about", "owns_process")
_THING_TYPES = ("topic", "process")


@dataclass
class SaveReport:
    """Qué pasó al guardar, para contárselo a la persona."""

    added: int = 0
    unchanged: int = 0
    status_changed: int = 0
    conflicts: int = 0
    ignored: int = 0  # negaciones de algo que no estaba en el grafo
    # Estado final de cada relación recibida, en el mismo orden. None: no se guardó
    statuses: list[int | None] = field(default_factory=list)
    # Lo que se dedujo al guardar porque la cosa ya tenía su herramienta anotada
    deduced: list[KnowledgeTriple] = field(default_factory=list)

    def summary(self) -> str:
        partes = [
            (self.added, "nueva", "nuevas"),
            (self.unchanged, "ya estaba", "ya estaban"),
            (self.status_changed, "pasó a pendiente", "pasaron a pendiente"),
            (self.conflicts, "conflicto", "conflictos"),
            (self.ignored, "negación sin relación previa", "negaciones sin relación previa"),
        ]
        texto = ", ".join(f"{n} {uno if n == 1 else varios}" for n, uno, varios in partes if n)
        return texto or "nada para guardar"


def load_graph(path: Path | None = None) -> dict:
    path = path or GRAPH_PATH
    if not path.exists():
        return {"nodes": [], "edges": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_triples(triples: list[KnowledgeTriple], path: Path | None = None) -> SaveReport:
    path = path or GRAPH_PATH
    graph = load_graph(path)
    report = SaveReport()
    now = datetime.now().isoformat(timespec="seconds")
    edges = [_add(graph, triple, now, report) for triple in triples]
    # Al final: un conflicto con una relación posterior cambia el estado de una anterior
    report.statuses = [None if edge is None else edge["status"] for edge in edges]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def save_tool(
    thing: str, tool: str, evidence: str, path: Path | None = None
) -> list[KnowledgeTriple]:
    """Anota que `thing` se hace con `tool` ("el tablero de Gestión es de Superset") y
    devuelve lo que se deduce del grafo: quien ya hace o sabe de esa cosa, sabe de la
    herramienta. Esas relaciones no se guardan acá: las guarda quien llama, con
    `save_triples`, para poder contarlas.

    El dato queda en el nodo de la cosa (`tool` y `tool_evidence`). Si todavía no hay
    nodo, se crea, así cuando alguien diga después que la hace, `save_triples` deduce
    la herramienta en ese momento (el otro orden). Lo rechazado y lo que ya es
    deducido no cuentan."""
    path = path or GRAPH_PATH
    graph = load_graph(path)
    nodes = _things_named(graph, thing)
    if not nodes:
        node = {"id": _key(thing), "type": "topic", "name": thing}
        graph["nodes"].append(node)
        nodes = [node]
    for node in nodes:
        node.setdefault("attributes", {}).update({"tool": tool, "tool_evidence": evidence})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    names = {n["id"]: n["name"] for n in graph["nodes"]}
    return [
        _tool_triple(names[e["source"]], e, node, evidence)
        for node in nodes
        for e in graph["edges"]
        if e["target"] == node["id"]
        and e["relation"] in _DOES
        and e["status"] != REJECTED
        and not e.get("inferred")
    ]


def _things_named(graph: dict, thing: str) -> list[dict]:
    """Los temas y procesos del grafo que son esa cosa: las mismas palabras, sin
    tildes ni plural ("tableros de gestión" es "tablero de Gestión"), aunque alguna
    tenga un error de tipeo de una letra ("tablero de gestió")."""
    wanted = _words(thing)
    return [
        n
        for n in graph["nodes"]
        if n["type"] in _THING_TYPES
        and (_key(n["name"]) == _key(thing) or _same_words(_words(n["name"]), wanted))
    ]


def _words(text: str) -> frozenset[str]:
    # Las palabras que dicen algo (4 letras o más), sin plural
    plain = _key(text).split("-")
    return frozenset(
        w[:-2] if w.endswith("es") and len(w) > 5 else w.rstrip("s") for w in plain if len(w) >= 4
    )


def _same_words(these: frozenset[str], those: frozenset[str]) -> bool:
    """Las mismas palabras, una por una, con una letra de diferencia como mucho en
    las largas (5 letras o más): de más, de menos o cambiada."""
    if not these or len(these) != len(those):
        return False
    rest = set(those)
    for word in these:
        match = next(
            (
                w
                for w in rest
                if w == word or (min(len(w), len(word)) >= 5 and _one_letter(w, word))
            ),
            None,
        )
        if match is None:
            return False
        rest.discard(match)
    return True


def _one_letter(a: str, b: str) -> bool:
    """¿Difieren en una sola letra (de más, de menos o cambiada)?"""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b, strict=True)) == 1
    short, long = sorted((a, b), key=len)
    return any(long[:i] + long[i + 1 :] == short for i in range(len(long)))


def _tool_triple(person: str, edge: dict, node: dict, evidence: str) -> KnowledgeTriple:
    """La relación deducida: quien hace la cosa sabe de su herramienta. Baja y
    pendiente, con el motivo para quien revisa."""
    attributes = node.get("attributes", {})
    tool, said = attributes["tool"], attributes.get("tool_evidence", "")
    did = f"{_RELATION_NAMES[edge['relation']]} {node['name']} (#{edge['id']})"
    return KnowledgeTriple(
        person,
        "knows_about",
        tool,
        evidence,
        "low",
        subject_id=edge["source"],
        needs_review=True,
        review_note=f"deducido: {did}, y {node['name']} se hace con {tool} («{said}»)",
        inferred=True,
    )


def _key(name: str) -> str:
    # "Compra de lápices" y "compra de lapices " son el mismo nodo
    sin_tildes = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sin_tildes.lower()).strip("-")


def rename_person(person_id: str, new: str, path: Path | None = None) -> bool:
    """Le pone a una persona del grafo un nombre más completo: "Diego Fernandez" pasa
    a "Diego Fernandes Hamilton". El id queda igual, así que sus aristas no cambian.
    Si no hay una persona con ese id, no hace nada. Devuelve si renombró."""
    path = path or GRAPH_PATH
    graph = load_graph(path)
    node = next(
        (n for n in graph["nodes"] if n["id"] == _key(person_id) and n["type"] == "person"),
        None,
    )
    if node is None or not new.strip():
        return False
    node["name"] = new
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def save_possible_match(
    name: str,
    candidate: str,
    evidence: str,
    score: float,
    confidence: float,
    path: Path | None = None,
    name_id: str = "",
    candidate_id: str = "",
) -> dict:
    """Vincula a dos personas que pueden ser la misma, para que alguien lo valide.

    La arista `may_be_same` lleva el peso de la duda: `weight` es el score de
    similitud y `confidence` la del modelo. Siempre queda pendiente. Si el par ya
    estaba vinculado (en cualquier dirección), no se duplica: suma la frase al
    historial y se queda con el peso mayor. `name_id` y `candidate_id`: los ids de
    los nodos, si no salen del nombre (un homónimo).
    Al aprobarla (`review`), los dos nodos se unen en uno; al rechazarla, el par queda
    rechazado y no se vuelve a preguntar.
    """
    path = path or GRAPH_PATH
    graph = load_graph(path)
    now = datetime.now().isoformat(timespec="seconds")
    source, target = _key(name_id or name), _key(candidate_id or candidate)
    _ensure_node(graph, source, "person", name)
    _ensure_node(graph, target, "person", candidate)
    edge = next(
        (
            e
            for e in graph["edges"]
            if e["relation"] == "may_be_same" and {e["source"], e["target"]} == {source, target}
        ),
        None,
    )
    if edge is None:
        edge = _new_edge(graph, source, "may_be_same", target, evidence, PENDING, now)
        edge["weight"], edge["confidence"] = score, confidence
    else:
        edge["history"].append({"status": edge["status"], "evidence": evidence, "at": now})
        if score > edge["weight"]:
            edge["weight"], edge["confidence"] = score, confidence
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return edge


@dataclass(frozen=True)
class Review:
    """Algo del grafo que espera que una persona lo apruebe o lo rechace."""

    edge_id: int  # el id que se le pasa a `review`
    # "relation": una relación; "same_person": ¿son la misma persona?; "conflict": una
    # de dos relaciones que chocan (aprobar una rechaza la otra)
    kind: Literal["relation", "same_person", "conflict"]
    summary: str  # "Diego es responsable de compra de lápices"
    evidence: str
    criticality: str  # vacío en las dudas de identidad
    # El score de la duda, o con qué relación choca y la nota del agente si la dejó
    # ("no coincide con su puesto…")
    detail: str
    created_at: str
    # De quién es la relación (vacío en las dudas de identidad) y su organización, si
    # su nodo la tiene. La del organigrama no está acá: es `person_profile`
    person_id: str = ""
    organization: str = ""


def pending_reviews(path: Path | None = None) -> list[Review]:
    """Lo que espera revisión, en el orden en que entró al grafo."""
    graph = load_graph(path)
    names = {n["id"]: n["name"] for n in graph["nodes"]}
    organizations = {
        n["id"]: n.get("attributes", {}).get("organization", "") for n in graph["nodes"]
    }
    rivals = _rivals(graph)
    reviews = []
    for e in graph["edges"]:
        # Las aristas de un conflicto son parte del grafo, no algo para revisar
        if e["status"] != PENDING or e["relation"] == "contradicts":
            continue
        source, target = names.get(e["source"], e["source"]), names.get(e["target"], e["target"])
        person_id = ""
        if e["relation"] == "may_be_same":
            kind, summary = "same_person", f"¿{source} es {target}?"
            detail = f"score {_number(e['weight'])} · confianza {_number(e['confidence'])}"
        else:
            kind = "conflict" if e["id"] in rivals else "relation"
            summary = f"{source} {_RELATION_NAMES.get(e['relation'], e['relation'])} {target}"
            clashes = [f"choca con #{r}" for r in rivals.get(e["id"], [])]
            # La nota del agente (por ejemplo, que no encaja con su puesto), si la tiene
            detail = ", ".join([*clashes, *([e["review_note"]] if e.get("review_note") else [])])
            person_id = e["source"]
        reviews.append(
            Review(
                e["id"],
                kind,
                summary,
                e["evidence"],
                e.get("criticality", ""),
                detail,
                e["created_at"],
                person_id,
                organizations.get(person_id, ""),
            )
        )
    return reviews


def review(edge_id: int, approve: bool, path: Path | None = None) -> str:
    """Aprueba o rechaza lo que espera revisión y cuenta qué pasó.

    - Una relación: pasa a confirmada o a rechazada.
    - Una duda de identidad: al aprobarla, las dos personas se unen en un nodo (el
      que ya existía, con el nombre más completo); al rechazarla, son distintas.
    - Una relación en conflicto: al aprobarla, la que choca se rechaza; al
      rechazarla, la otra queda pendiente como cualquier relación. El conflicto se
      cierra.

    La decisión queda en el `history` de la arista.
    """
    path = path or GRAPH_PATH
    graph = load_graph(path)
    edge = next((e for e in graph["edges"] if e["id"] == edge_id), None)
    if edge is None or edge["status"] != PENDING or edge["relation"] == "contradicts":
        raise ValueError(f"No hay nada pendiente de revisar con el id {edge_id}.")
    now = datetime.now().isoformat(timespec="seconds")
    names = {n["id"]: n["name"] for n in graph["nodes"]}

    if edge["relation"] == "may_be_same":
        source, target = names[edge["source"]], names[edge["target"]]
        if approve:
            moved = _merge_people(graph, edge["source"], edge["target"])
            message = f"Unifiqué a {source} con {target}: {moved} relaciones movidas."
        else:
            _decide(edge, REJECTED, now)
            message = f"{source} y {target} son personas distintas: no se vuelve a preguntar."
    else:
        rivals = _rivals(graph).get(edge_id, [])
        _decide(edge, CONFIRMED if approve else REJECTED, now)
        message = f"Relación #{edge_id} {'aprobada' if approve else 'rechazada'}."
        if approve:
            for rival in (e for e in graph["edges"] if e["id"] in rivals):
                _decide(rival, REJECTED, now)
            if rivals:
                message += f" Rechacé la que chocaba: #{', #'.join(map(str, rivals))}."
        if rivals:
            _close_conflicts(graph, edge_id)

    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return message


def set_organization(person_id: str, organization: str, path: Path | None = None) -> bool:
    """Le pone a una persona del grafo la organización a la que pertenece, la que
    dijo quien revisa. Si no hay una persona con ese id o la organización está
    vacía, no hace nada. Devuelve si la guardó."""
    path = path or GRAPH_PATH
    graph = load_graph(path)
    node = next(
        (n for n in graph["nodes"] if n["id"] == _key(person_id) and n["type"] == "person"),
        None,
    )
    if node is None or not organization.strip():
        return False
    node.setdefault("attributes", {})["organization"] = organization.strip()
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def _number(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def _decide(edge: dict, status: int, now: str) -> None:
    edge["status"] = status
    decision = {CONFIRMED: "aprobada", REJECTED: "rechazada"}[status]
    edge["history"].append({"status": status, "evidence": f"revisión: {decision}", "at": now})


def _rivals(graph: dict) -> dict[int, list[int]]:
    """Por relación en un conflicto abierto, las relaciones con las que choca."""
    rivals: dict[int, list[int]] = {}
    for node in graph["nodes"]:
        if node["type"] == "conflict":
            ids = node["attributes"]["edges"]
            for edge_id in ids:
                rivals.setdefault(edge_id, []).extend(i for i in ids if i != edge_id)
    return rivals


def _close_conflicts(graph: dict, edge_id: int) -> None:
    """Borra los conflictos de esa relación y sus aristas `contradicts`: ya se decidió."""
    closed = {
        n["id"]
        for n in graph["nodes"]
        if n["type"] == "conflict" and edge_id in n["attributes"]["edges"]
    }
    graph["nodes"] = [n for n in graph["nodes"] if n["id"] not in closed]
    graph["edges"] = [e for e in graph["edges"] if e["source"] not in closed]


def _merge_people(graph: dict, gone: str, kept: str) -> int:
    """Une a la persona `gone` en `kept`: le pasa sus relaciones (sin duplicar), su
    puesto y empresa si `kept` no los tiene, y su nombre si es más completo. Borra el
    nodo de `gone` y las dudas entre las dos. Devuelve cuántas relaciones movió."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    old, new = nodes[gone], nodes[kept]
    if len(old["name"].split()) > len(new["name"].split()):
        new["name"] = old["name"]
    for name, value in old.get("attributes", {}).items():
        new.setdefault("attributes", {}).setdefault(name, value)

    between = {gone, kept}
    moved = set()
    edges = []
    for e in graph["edges"]:
        if e["relation"] == "may_be_same" and {e["source"], e["target"]} == between:
            continue  # la duda ya se resolvió
        if gone in (e["source"], e["target"]):
            e["source"] = kept if e["source"] == gone else e["source"]
            e["target"] = kept if e["target"] == gone else e["target"]
            moved.add(e["id"])
        edges.append(e)

    # Si las dos tenían la misma relación, queda una: la de mejor estado, con las dos
    # historias
    best = [REJECTED, PENDING, CONFIRMED].index
    unique: dict[tuple, dict] = {}
    for e in edges:
        key = (e["source"], e["relation"], e["target"])
        if key not in unique:
            unique[key] = e
            continue
        twin = unique[key]
        if best(e["status"]) > best(twin["status"]):
            twin["status"] = e["status"]
        twin["history"] += e["history"]
        moved.discard(e["id"])
    graph["edges"] = list(unique.values())
    graph["nodes"] = [n for n in graph["nodes"] if n["id"] != gone]
    return len(moved & {e["id"] for e in graph["edges"]})


def _add(graph: dict, triple: KnowledgeTriple, now: str, report: SaveReport) -> dict | None:
    """Da de alta la relación y devuelve su arista en el grafo (None si no se guardó)."""
    # El id sale del nombre, salvo que el agente diga de qué nodo se habla (homónimos)
    source = _key(triple.subject_id or triple.subject)
    target = _key(triple.object_id or triple.object)
    wanted = {(source, triple.relation, target)}
    if triple.relation in _SYMMETRIC:
        wanted.add((target, triple.relation, source))
    same = next(
        (e for e in graph["edges"] if (e["source"], e["relation"], e["target"]) in wanted),
        None,
    )

    if triple.negated:
        # El grafo registra conocimiento, no ausencias: negar algo que no está no se guarda
        if same is None:
            report.ignored += 1
            return None
        if same["status"] == REJECTED:  # ya se descartó: no hay nada que revisar
            report.unchanged += 1
            return same
        same["status"] = PENDING
        same["history"].append({"status": PENDING, "evidence": triple.evidence, "at": now})
        report.status_changed += 1
        return same

    if same is not None:
        _set_attributes(graph, source, triple)
        if same.get("inferred") and not triple.inferred:
            # Lo dicho le gana a lo deducido: la relación pasa a ser dicha, con su frase
            _now_said(same, triple, now)
            report.status_changed += 1
        else:
            report.unchanged += 1
        return same

    _ensure_node(graph, source, "person", triple.subject)
    _set_attributes(graph, source, triple)
    _ensure_node(graph, target, _TARGET_TYPE[triple.relation], triple.object)
    # Lo de criticidad baja entra confirmado, salvo que pida revisión; lo de media y
    # alta, una persona lo revisa
    status = CONFIRMED if triple.criticality == "low" and not triple.needs_review else PENDING
    edge = _new_edge(graph, source, triple.relation, target, triple.evidence, status, now)
    edge["criticality"] = triple.criticality
    edge["exclusive"] = triple.exclusive
    if triple.review_note:
        edge["review_note"] = triple.review_note
    if triple.inferred:
        edge["inferred"] = True
    report.added += 1

    # El otro orden: la cosa ya tenía anotada su herramienta ("el tablero de Gestión
    # es de Superset") y ahora alguien dice que la hace. Lo deducido se suma solo
    target_node = next(n for n in graph["nodes"] if n["id"] == target)
    if (
        triple.relation in _DOES
        and not triple.inferred
        and target_node.get("attributes", {}).get("tool")
    ):
        deduced = _tool_triple(triple.subject, edge, target_node, triple.evidence)
        before = report.added
        _add(graph, deduced, now, report)
        if report.added > before:  # si ya estaba (dicha o deducida), no se cuenta
            report.deduced.append(deduced)

    rivals = [
        e
        for e in graph["edges"]
        if e["relation"] == triple.relation
        and e["target"] == target
        and e["source"] != source
        and e["status"] != REJECTED
        and (e.get("exclusive") or triple.exclusive)
    ]
    for rival in rivals:
        _add_conflict(graph, rival, edge, now)
        report.conflicts += 1
    return edge


def _now_said(edge: dict, triple: KnowledgeTriple, now: str) -> None:
    """Una relación deducida que ahora alguien dijo: deja de ser deducida, toma la frase
    y la criticidad de lo dicho y, si seguía pendiente, el estado que le toca a lo dicho."""
    edge.pop("inferred", None)
    edge.pop("review_note", None)
    edge["evidence"], edge["criticality"] = triple.evidence, triple.criticality
    if triple.review_note:
        edge["review_note"] = triple.review_note
    if edge["status"] == PENDING and triple.criticality == "low" and not triple.needs_review:
        edge["status"] = CONFIRMED
    edge["history"].append({"status": edge["status"], "evidence": triple.evidence, "at": now})


def _add_conflict(graph: dict, first: dict, second: dict, now: str) -> None:
    for edge, other in ((first, second), (second, first)):
        edge["status"] = PENDING
        edge["history"].append({"status": PENDING, "evidence": other["evidence"], "at": now})

    target_name = next(n["name"] for n in graph["nodes"] if n["id"] == first["target"])
    n = sum(1 for node in graph["nodes"] if node["type"] == "conflict") + 1
    conflict_id = f"conflicto-{n}"
    graph["nodes"].append(
        {
            "id": conflict_id,
            "type": "conflict",
            "name": f"Conflicto: {target_name}",
            "attributes": {
                "edges": [first["id"], second["id"]],
                "evidence": [first["evidence"], second["evidence"]],
            },
        }
    )
    for edge in (first, second):
        _new_edge(graph, conflict_id, "contradicts", edge["source"], edge["evidence"], PENDING, now)


def _ensure_node(graph: dict, node_id: str, node_type: str, name: str) -> None:
    if not any(n["id"] == node_id for n in graph["nodes"]):
        graph["nodes"].append({"id": node_id, "type": node_type, "name": name})


def _set_attributes(graph: dict, node_id: str, triple: KnowledgeTriple) -> None:
    # Puesto y empresa de la persona, si la frase los dijo: gana el último que se dijo
    said = {"position": triple.subject_position, "organization": triple.subject_organization}
    said = {field: value.strip() for field, value in said.items() if value.strip()}
    if said:
        node = next(n for n in graph["nodes"] if n["id"] == node_id)
        node.setdefault("attributes", {}).update(said)


def _new_edge(
    graph: dict, source: str, relation: str, target: str, evidence: str, status: int, now: str
) -> dict:
    edge = {
        "id": max((e["id"] for e in graph["edges"]), default=0) + 1,
        "source": source,
        "relation": relation,
        "target": target,
        "evidence": evidence,
        "status": status,
        "history": [],
        "created_at": now,
    }
    graph["edges"].append(edge)
    return edge

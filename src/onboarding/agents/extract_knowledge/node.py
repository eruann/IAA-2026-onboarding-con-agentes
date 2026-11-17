# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Nodo de la red informal. Titular: rol Grafo cultural y datos.

Saca del texto las relaciones "quién sabe qué" (`extract_triples`, con sus
instrucciones en `extraction_prompt.md`), cada una con la frase que la respalda,
las guarda (`save_triples`) y devuelve la lista. La respuesta la arma el código,
no el modelo: nada de preguntas ni comentarios, solo lo que encontró. Si el texto
pregunta "¿quién sabe de X?" o "¿cómo se
hace X?", responde con el grafo (`what_is_known_about`, que si el tema no está
tal cual busca los cercanos) en vez de extraer. La forma de una relación
(`KnowledgeTriple`) y las consultas al grafo están en la knowledge layer.
"""

import re
import unicodedata
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import get_args

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from onboarding.agents.common import Models, Node, NodeSpec
from onboarding.agents.extract_knowledge.identity import (
    PersonMatch,
    invoke_structured,
    resolve_person,
)
from onboarding.agents.state import OnboardingState
from onboarding.knowledge import (
    Criticality,
    Expert,
    KnowledgeTriple,
    Relation,
    document_names,
    person_profile,
    read_documents,
    rename_person,
    save_possible_match,
    save_tool,
    save_triples,
    what_is_known_about,
)
from onboarding.llm import get_structured_model, load_prompt
from onboarding.paths import CORPUS_DIR

PROMPT = Path(__file__).with_name("prompt.md")  # el del agente
EXTRACTION_PROMPT = Path(__file__).with_name("extraction_prompt.md")  # el de extract_triples
ROLE_FIT_PROMPT = Path(__file__).with_name("role_fit_prompt.md")  # el de _review_if_off_role
# Las relaciones que dicen qué hace o sabe una persona: las que pueden chocar con su puesto
_ROLE_RELATIONS = ("owns_process", "knows_about")
# Las relaciones cuyo objeto también es una persona: se resuelve como el sujeto
_PERSON_RELATIONS = ("introduced", "works_with")
ORG_CHART = "organigrama.md"

RELATIONS = {
    "knows_about": "sabe de",
    "introduced": "presentó a",
    "belongs_to": "pertenece a",
    "owns_process": "es responsable de",
    "works_with": "trabaja con",
}
CRITICALITIES = {"high": "alta", "medium": "media", "low": "baja"}
# Estado en el grafo después de guardar (store.py): 0 pendiente, 1 confirmado
STATUSES = {0: "pendiente", 1: "confirmada", None: "no guardada"}

# "¿Quién sabe de impuestos?", "¿quién es el que más sabe de IVA?", "quienes se
# encargan del backup?", "¿cómo se recupera el backup?": el tema va hasta el "?"
_QUESTION = re.compile(
    r"(?:qui[eé]n(?:es)?\s+(?:es\s+(?:el|la)\s+que\s+)?(?:m[aá]s\s+)?"
    r"(?:sabe|conoce|maneja|se\s+encarga|es\s+responsable)n?"
    r"\s+(?:m[aá]s\s+)?(?:de\s+|del\s+|sobre\s+|con\s+)?"
    r"|c[oó]mo\s+(?:se\s+|hago\s+|hacemos\s+|puedo\s+)?)(?P<topic>[^?]+)",
    re.IGNORECASE,
)

# Lo que tiene que devolver el modelo, como JSON Schema: los mismos campos que
# KnowledgeTriple. Con un dict, with_structured_output devuelve dicts.
_SCHEMA = {
    "title": "extraccion",
    "description": "Relaciones dichas explícitamente en el texto.",
    "type": "object",
    "properties": {
        "triples": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "relation": {"type": "string", "enum": list(get_args(Relation))},
                    "object": {"type": "string"},
                    "evidence": {
                        "type": "string",
                        "description": "Frase copiada textual del texto, sin cambios.",
                    },
                    "criticality": {
                        "type": "string",
                        "enum": list(get_args(Criticality)),
                        "description": "Impacto si se pierde este conocimiento.",
                    },
                    "negated": {
                        "type": "boolean",
                        "description": "La frase niega la relación.",
                    },
                    "exclusive": {
                        "type": "boolean",
                        "description": "La frase dice que el sujeto es el único.",
                    },
                    "subject_position": {
                        "type": "string",
                        "description": "Puesto del sujeto, si el texto lo dice; si no, vacío.",
                    },
                    "subject_organization": {
                        "type": "string",
                        "description": "Empresa del sujeto, si el texto lo dice; si no, vacío.",
                    },
                },
                "required": [
                    "subject",
                    "relation",
                    "object",
                    "evidence",
                    "criticality",
                    "negated",
                    "exclusive",
                    "subject_position",
                    "subject_organization",
                ],
            },
        },
        # Lo deducido va aparte: la herramienta de algo que alguien hizo
        "inferred": {
            "type": "array",
            "description": "Herramientas que se deducen de algo que la persona hizo.",
            "items": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "tool": {
                        "type": "string",
                        "description": "La herramienta o tecnología, como la nombra la fuente.",
                    },
                    "evidence": {
                        "type": "string",
                        "description": "Frase textual de lo que hizo, copiada sin cambios.",
                    },
                    "source": {
                        "type": "string",
                        "description": (
                            "Dónde dice con qué herramienta se hace: «conversación» o el "
                            "nombre del documento de <procedimientos>."
                        ),
                    },
                    "reason": {
                        "type": "string",
                        "description": "Qué hizo y con qué se hace eso, en una línea.",
                    },
                },
                "required": ["subject", "tool", "evidence", "source", "reason"],
            },
        },
        # Con qué herramienta se hace algo, aunque no nombre a nadie: se cruza con el grafo
        "tool_facts": {
            "type": "array",
            "description": "Con qué herramienta se hace algo, aunque la frase no nombre a nadie.",
            "items": {
                "type": "object",
                "properties": {
                    "thing": {
                        "type": "string",
                        "description": "La tarea, el informe o el proceso, como lo dice la frase.",
                    },
                    "tool": {"type": "string", "description": "La herramienta, como la nombra."},
                    "evidence": {
                        "type": "string",
                        "description": "Frase textual que lo dice, copiada sin cambios.",
                    },
                },
                "required": ["thing", "tool", "evidence"],
            },
        },
    },
    "required": ["triples", "inferred", "tool_facts"],
}
CONVERSATION = "conversación"


@lru_cache
def _org_chart() -> str:
    return (CORPUS_DIR / ORG_CHART).read_text(encoding="utf-8")


@lru_cache
def _procedures() -> str:
    # Todo el corpus menos el organigrama, que va aparte
    return read_documents(_procedure_names())


def _procedure_names() -> tuple[str, ...]:
    return tuple(name for name in document_names() if name != ORG_CHART)


# De ahí sale la criticidad (extraction_prompt.md): va siempre
WELCOME = "bienvenida.md"
# Palabras que están en casi cualquier frase o documento: no sirven para elegir
_STOPWORDS = frozenset(
    "tiene tienen sabe saben encarga encargan cuando donde porque desde hasta sobre "
    "entre todos todas siempre tambien ademas despues antes ahora mismo misma mismos "
    "puede pueden hacer hace hacen quien quienes cual cuales estos estas otros otras "
    "preguntale pregunta conoce conocen esta estan para".split()
)


@lru_cache
def _words_of(name: str) -> frozenset[str]:
    return frozenset(_stem(w) for w in _words((CORPUS_DIR / name).read_text(encoding="utf-8")))


def _words(text: str) -> list[str]:
    return [_plain(w) for w in re.findall(r"[^\W\d_]+", text)]


def _stem(word: str) -> str:
    # Sin plural: "pagos" y "pago", "gestiones" y "gestion" son la misma palabra
    if word.endswith("es") and len(word) > 5:
        return word[:-2]
    return word[:-1] if word.endswith("s") else word


def _grep_procedures(text: str) -> tuple[str, ...]:
    """Los procedimientos que nombran alguna palabra de la conversación (5 letras o
    más, sin tildes ni plural), más bienvenida.md. Si ninguno la nombra, todos: el
    modelo tiene que poder confirmar que lo que se dijo no está escrito."""
    wanted = {_stem(w) for w in _words(text) if len(w) >= 5 and w not in _STOPWORDS}
    names = _procedure_names()
    found = tuple(n for n in names if n != WELCOME and wanted & _words_of(n))
    if not found:
        return names
    return tuple(n for n in names if n == WELCOME or n in found)


# recorrido: extraccion
@dataclass(frozen=True)
class ToolFact:
    """Con qué herramienta se hace algo: "el tablero de Gestión es de Superset"."""

    thing: str
    tool: str
    evidence: str


def extract_triples(text: str, model: BaseChatModel | None = None) -> list[KnowledgeTriple]:
    """Las relaciones del texto, dichas y deducidas, cada una con su frase."""
    return _extract(text, model)[0]


def _extract(
    text: str, model: BaseChatModel | None = None
) -> tuple[list[KnowledgeTriple], list[ToolFact]]:
    """Las relaciones y, aparte, con qué herramienta se hace algo (`ToolFact`), que el
    nodo cruza con el grafo para deducir quién sabe de esa herramienta."""
    # Sin modelo explícito, el del perfil estructurado (regla 5). Pasar uno sirve para
    # probar con otro modelo o, en los tests, con uno de salida fija.
    model = model or get_structured_model()
    # json_schema: el proveedor restringe la salida al esquema. Con function_calling
    # los modelos chicos (qwen2.5 7B en Ollama) inventan sus propios argumentos.
    # El organigrama y los procedimientos van con el prompt: sin verlos, el modelo
    # no puede saber qué relaciones ya están escritas y tiene que descartar. De los
    # procedimientos, primero un grep: solo los que nombran algo de la conversación;
    # si no encuentra nada, todos.
    system = (
        f"{load_prompt(EXTRACTION_PROMPT)}\n"
        f"<organigrama>\n{_org_chart()}\n</organigrama>\n"
        f"<procedimientos>\n{read_documents(_grep_procedures(text))}\n</procedimientos>"
    )
    # Si la respuesta no entra en el tope de salida, se reintenta con más lugar
    output = invoke_structured(model, _SCHEMA, [SystemMessage(system), HumanMessage(text)])
    # Nada de deducir: si la frase de respaldo no está en el texto, el modelo la
    # inventó o la parafraseó, y la relación no va al grafo.
    triples = [t for t in (output or {}).get("triples", []) if t["evidence"] in text]
    for triple in triples:
        # Lo mismo con la organización: solo si la nombra la frase de respaldo
        organization = triple.get("subject_organization", "")
        if organization.casefold() not in triple["evidence"].casefold():
            triple["subject_organization"] = ""
        # Y el nombre, completo: el modelo a veces recorta los apellidos
        triple["subject"] = _full_name(triple["subject"], triple["evidence"])
        # Y el objeto, con las palabras de la frase: el modelo a veces las "corrige"
        triple["object"] = _as_said(triple["object"], triple["evidence"])
    said = [KnowledgeTriple(**triple) for triple in triples]
    inferred = output.get("inferred", []) if isinstance(output, dict) else []
    facts = output.get("tool_facts", []) if isinstance(output, dict) else []
    return said + _inferred(inferred, text, said), _tool_facts(facts, text)


def _tool_facts(items: list, text: str) -> list[ToolFact]:
    """Los mismos controles que lo dicho: la frase textual, y la cosa y la herramienta
    nombradas en ella. Si no, el modelo lo armó y no va."""
    facts = []
    for item in items:
        try:
            thing, tool = str(item["thing"]).strip(), str(item["tool"]).strip()
            evidence = str(item["evidence"])
        except (KeyError, TypeError):
            continue
        said = set(_words(evidence))
        if not thing or not tool or evidence not in text:
            continue
        if not set(_words(tool)) <= said or not set(_words(thing)) <= said:
            continue
        facts.append(ToolFact(_as_said(thing, evidence), tool, evidence))
    return facts


def _inferred(items: list, text: str, said: list[KnowledgeTriple]) -> list[KnowledgeTriple]:
    """Lo deducido, como relaciones `knows_about` de criticidad baja, pendientes y con
    el motivo para quien revisa. Con los mismos controles que lo dicho: la frase de lo
    que hizo tiene que estar textual, y la herramienta, nombrada en la conversación o
    en el procedimiento que se cita; si no, el modelo la inventó y no va. Si lo mismo
    ya se dijo en la conversación, no se repite como deducido."""
    known = {(_plain(t.subject), _plain(t.object)) for t in said if t.relation == "knows_about"}
    procedures = _procedure_names()
    result = []
    for item in items:
        try:
            subject, tool = str(item["subject"]).strip(), str(item["tool"]).strip()
            evidence, source = str(item["evidence"]), str(item["source"]).strip()
            reason = str(item.get("reason", "")).strip()
        except (KeyError, TypeError):
            continue  # un ítem roto no frena a los demás
        if not subject or not tool or evidence not in text:
            continue
        if source in procedures:
            where = (CORPUS_DIR / source).read_text(encoding="utf-8")
            said_by = f"lo dice {source}"
        else:
            where, said_by = text, "lo dice la conversación"
        if not set(_words(tool)) <= set(_words(where)):
            continue
        subject = _full_name(subject, evidence)
        if (_plain(subject), _plain(tool)) in known:
            continue
        known.add((_plain(subject), _plain(tool)))
        note = f"deducido: {reason}" if reason else "deducido"
        result.append(
            KnowledgeTriple(
                subject,
                "knows_about",
                tool,
                evidence,
                "low",
                needs_review=True,
                review_note=f"{note} ({said_by})",
                inferred=True,
            )
        )
    return result


def _as_said(text: str, evidence: str) -> str:
    """Las palabras de `text` como las dice la frase: el modelo a veces corrige un
    nombre que no conoce ("banco micro" -> "banco macro"). Una palabra que no está en
    la frase y difiere en una sola letra de una que sí, se cambia por esa. Las cortas
    ("la", "le") y lo que el modelo resumió con otras palabras quedan como vinieron."""
    said = {_plain(w): w for w in re.findall(r"[^\W\d_]+", evidence)}

    def fix(match: re.Match) -> str:
        word = _plain(match.group())
        if len(word) < 4 or word in said:
            return match.group()
        close = [
            w
            for plain, w in said.items()
            if len(plain) == len(word)
            and sum(a != b for a, b in zip(plain, word, strict=True)) == 1
        ]
        return close[0] if len(close) == 1 else match.group()

    return re.sub(r"[^\W\d_]+", fix, text)


def _full_name(name: str, evidence: str) -> str:
    """El nombre como sigue en la frase, con los apellidos que el modelo recortó:
    "Diego Fernandez" en "…del Banco Diego Fernandez Halmitón debido a…" es "Diego
    Fernandez Halmitón". Suma las palabras con mayúscula que vienen justo después;
    una coma o una minúscula cortan. Si no lo encuentra, queda como vino."""
    words = list(re.finditer(r"[^\W\d_]+", evidence))
    wanted = [_plain(w) for w in name.split()]
    n = len(wanted)
    for i in range(len(words) - n + 1):
        if not n or [_plain(w.group()) for w in words[i : i + n]] != wanted:
            continue
        end = i + n
        while (
            end < len(words)
            and words[end].group()[0].isupper()
            and not evidence[words[end - 1].end() : words[end].start()].strip()
        ):
            end += 1
        return evidence[words[i].start() : words[end - 1].end()] if end > i + n else name
    return name


def _plain(word: str) -> str:
    # Sin tildes ni mayúsculas: "Fernández" y "fernandez" son la misma palabra
    return unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode().casefold()


def _resolve(
    triples: list[KnowledgeTriple], model: BaseChatModel
) -> tuple[list[KnowledgeTriple], list[PersonMatch], dict[str, str]]:
    """Cada persona nombrada, contra las que ya se conocen (`resolve_person`): si es
    la misma, la relación se guarda en el nodo que ya existe y no se duplica. Si la
    mención trae un nombre más completo, el nodo pasa a llamarse así (`renamed`:
    nombre anterior -> nuevo)."""
    matches: dict[str, PersonMatch] = {}
    for t in triples:
        mentions = [(t.subject, t.subject_position, t.subject_organization)]
        if t.relation in _PERSON_RELATIONS:  # el objeto también es una persona
            mentions.append((t.object, "", ""))
        for name, position, organization in mentions:
            if name not in matches:
                matches[name] = resolve_person(name, t.evidence, position, organization, model)

    renamed: dict[str, str] = {}
    for m in matches.values():
        if _is_fuller(m):
            # Si ya tiene nodo, se renombra; si no (alguien del organigrama que todavía
            # no está en el grafo), el nodo nace con el nombre más completo
            rename_person(m.candidate_id, m.name)
            renamed[m.candidate] = m.name

    def known_as(name: str) -> tuple[str, str]:
        saved, node_id = _saved_as(matches[name])
        return renamed.get(saved, saved), node_id

    resolved = []
    for t in triples:
        subject, subject_id = known_as(t.subject)
        obj, object_id = known_as(t.object) if t.relation in _PERSON_RELATIONS else (t.object, "")
        resolved.append(
            replace(t, subject=subject, subject_id=subject_id, object=obj, object_id=object_id)
        )
    return resolved, list(matches.values()), renamed


def _review_if_unplaced(triples: list[KnowledgeTriple]) -> list[KnowledgeTriple]:
    """Si no se sabe de qué organización es la persona (no está en el organigrama, la
    frase no lo dice y su nodo no lo tiene de antes), la relación queda pendiente para
    que alguien la revise, aunque sea de criticidad baja: la criticidad no cambia."""
    return [
        replace(t, needs_review=True)
        if not t.subject_organization and not person_profile(t.subject, t.subject_id).organization
        else t
        for t in triples
    ]


def _review_if_off_role(
    triples: list[KnowledgeTriple], model: BaseChatModel
) -> list[KnowledgeTriple]:
    """Si la tarea no encaja con el puesto oficial de la persona (Gerente de Calidad
    "se encarga de llamar a los clientes para cobrar"), la relación queda pendiente
    con una nota para quien la revisa. No se descarta: puede ser justo lo que el
    organigrama no muestra. Solo para gente del organigrama, que tiene puesto oficial;
    si el modelo no responde bien, quedan como estaban."""
    checked = {
        i: profile
        for i, t in enumerate(triples)
        # Lo deducido ya queda pendiente, con su propia nota
        if t.relation in _ROLE_RELATIONS and not t.negated and not t.inferred
        for profile in [person_profile(t.subject, t.subject_id)]
        if profile.internal and profile.position
    }
    if not checked:
        return triples
    schema = {
        "title": "encaje_puesto",
        "description": "Por relación: si la tarea encaja con el puesto oficial.",
        "type": "object",
        "properties": {
            "checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "enum": list(checked)},
                        "fits": {"type": "boolean"},
                        "reason": {"type": "string"},
                    },
                    "required": ["index", "fits", "reason"],
                },
            }
        },
        "required": ["checks"],
    }
    listing = "".join(
        f"{i}. {triples[i].subject} · puesto oficial: {profile.position} · "
        f"{RELATIONS[triples[i].relation]} {triples[i].object} · frase: «{triples[i].evidence}»\n"
        for i, profile in checked.items()
    )
    system = f"{load_prompt(ROLE_FIT_PROMPT)}\n<procedimientos>\n{_procedures()}\n</procedimientos>"
    question = HumanMessage(f"<relaciones>\n{listing}</relaciones>")
    output = invoke_structured(model, schema, [SystemMessage(system), question])
    notes = {}
    for item in output.get("checks", []) if isinstance(output, dict) else []:
        try:
            if item["index"] in checked and item["fits"] is False:
                position = checked[item["index"]].position
                reason = str(item.get("reason", "")).strip()
                notes[item["index"]] = f"no coincide con su puesto ({position})" + (
                    f": {reason}" if reason else ""
                )
        except (KeyError, TypeError):
            continue  # un ítem roto no frena a los demás
    return [
        replace(t, needs_review=True, review_note=notes[i]) if i in notes else t
        for i, t in enumerate(triples)
    ]


def _is_fuller(match: PersonMatch) -> bool:
    """¿La mención trae un nombre más completo (más palabras) que el guardado? Vale
    también para la gente del organigrama: su puesto sale del id, no del nombre."""
    return (
        match.decision == "same"
        and bool(match.candidate)
        and len(match.name.split()) > len(match.candidate.split())
    )


def _saved_as(match: PersonMatch) -> tuple[str, str]:
    """Con qué nombre y en qué nodo queda: el que ya existe si es la misma persona; si
    es otra que se llama igual, con su nombre en un nodo propio (`save_id`); si no,
    como vino (el id sale del nombre)."""
    if match.decision == "same" and match.candidate:
        return match.candidate, match.candidate_id
    return match.name, match.save_id


def _save_doubts(triples: list[KnowledgeTriple], matches: list[PersonMatch]) -> int:
    """Cada duda (`maybe`) queda en el grafo como una arista pendiente entre las dos
    personas, con el score como peso, para que alguien la valide. Devuelve cuántas."""
    doubts = [m for m in matches if m.decision == "maybe" and m.candidate]
    for m in doubts:
        name, node_id = _saved_as(m)
        evidence = next(t.evidence for t in triples if name in (t.subject, t.object))
        save_possible_match(
            name,
            m.candidate,
            evidence,
            m.score,
            m.confidence,
            name_id=node_id,
            candidate_id=m.candidate_id,
        )
    return len(doubts)


def _identity_notes(matches: list[PersonMatch], renamed: dict[str, str]) -> dict[str, str]:
    """Lo que se dice al lado de cada persona: con quién se unificó (y si tomó su
    nombre más completo) o con quién puede coincidir, con el score y la confianza."""

    def number(value: float) -> str:
        return f"{value:.2f}".replace(".", ",")

    notes = {}
    for m in matches:
        figures = f"score {number(m.score)} · confianza {number(m.confidence)}"
        if m.decision == "same" and m.candidate in renamed:
            new = renamed[m.candidate]
            notes[new] = f" (era «{m.candidate}»: ahora **{new}** · {figures})"
        elif m.decision == "same" and m.candidate and m.candidate != m.name:
            notes[m.candidate] = (
                f" (era «{m.name}»: es **{m.candidate}**, del {m.source} · {figures})"
            )
        elif m.decision == "maybe":
            notes[_saved_as(m)[0]] = (
                f" (¿será **{m.candidate}**, del {m.source}? {figures} · queda para validar)"
            )
    return notes


def _report(
    triples: list[KnowledgeTriple],
    statuses: list,
    summary: str,
    matches: list[PersonMatch] = (),
    renamed: dict[str, str] | None = None,
) -> str:
    """La respuesta del agente: las relaciones encontradas, sin modelo de por medio
    (nada de preguntas ni comentarios), y cómo quedó el grafo."""
    if not triples:
        return "No encontré relaciones con respaldo en el texto."
    notes = _identity_notes(list(matches), renamed or {})
    lines = [
        f"- {_with_position(person_profile(t.subject, t.subject_id))}{notes.get(t.subject, '')} "
        f"{'no ' if t.negated else ''}"
        f"{RELATIONS.get(t.relation, t.relation)} **{t.object}**"
        f"{' (deducida)' if t.inferred else ''} («{t.evidence}») · "
        f"criticidad {CRITICALITIES[t.criticality]} · {STATUSES[status]}"
        f"{f' · ⚠ {t.review_note}' if t.review_note else ''}"
        for t, status in zip(triples, statuses, strict=True)
    ]
    return (
        f"Encontré {len(triples)} relaciones:\n\n"
        + "\n".join(lines)
        + f"\n\nEn el grafo: {summary}."
    )


# recorrido: nodo-red-informal
def make_extract_knowledge(models: Models) -> Node:
    def extract_knowledge(state: OnboardingState) -> dict:
        # TODO(grafo): pasar de data/informal_network.json a nodes/edges, y correr
        # al final de cada conversación (no solo cuando se elige este nodo) sin
        # pisar la respuesta que ya dio otro agente.
        text = state.get("input", "")
        # Una pregunta se responde con el grafo; una conversación se extrae. Que
        # termine en "?" las distingue: "Diego, como siempre, sabe de Excel" se extrae
        if text.strip().endswith("?"):
            question = _QUESTION.search(text)
            topic = question["topic"] if question else text
            return _who_knows(topic.strip(" ¿?.!"), models.structured)
        extracted, facts = _extract(text, models.structured)
        triples, matches, renamed = _resolve(extracted, models.structured)
        triples = _review_if_unplaced(triples)
        triples = _review_if_off_role(triples, models.structured)
        # Con qué herramienta se hace algo: se anota en el grafo y, si alguien ya lo
        # hace, sabe de esa herramienta (deducido). Ya vienen con su persona resuelta
        triples += [t for f in facts for t in save_tool(f.thing, f.tool, f.evidence)]
        statuses, summary = [], ""
        if triples:
            report = save_triples(triples)
            # Lo que se dedujo al guardar: la cosa ya tenía su herramienta anotada
            triples += report.deduced
            statuses = report.statuses + [0] * len(report.deduced)
            summary = report.summary()
            doubts = _save_doubts(triples, matches)
            if doubts:
                summary += f", {doubts} posible misma persona para validar"
        output = _report(triples, statuses, summary, matches, renamed)
        if facts:
            noted = "\n".join(
                f"- **{f.thing}** se hace con **{f.tool}** («{f.evidence}»)" for f in facts
            )
            output = f"{output}\n\nAnoté en el grafo:\n{noted}"
        return {"output": output, "citations": [t.evidence for t in triples]}

    return extract_knowledge


def _who_knows(topic: str, model: BaseChatModel) -> dict:
    # Pregunta, no conversación: se responde con el grafo. Además de a quién
    # preguntarle, lo que se dijo: el procedimiento no escrito.
    facts = what_is_known_about(topic, model=model)
    intro = ""
    if facts and facts[0].nearby:
        # No estaba tal cual: son los temas cercanos que eligió el modelo
        related = list(dict.fromkeys(f.about for f in facts))
        about = ", ".join(f"**{name}**" for name in related)
        intro = f"No encontré «{topic}» en el grafo. Lo más cercano: {about}.\n\n"
        topic = ", ".join(related)
    if not facts:
        return {"output": f"No encontré a nadie en el grafo que sepa de {topic}.", "citations": []}
    people = {f.person_id: f.person for f in facts}  # por id: dos homónimos son dos
    lines = [f"- «{f.evidence}» ({f.person} · {STATUSES[1 if f.confirmed else 0]})" for f in facts]
    names = ", ".join(_with_position(person_profile(p, pid)) for pid, p in people.items())
    return {
        "output": f"{intro}De {topic} saben: {names}.\n\nLo que se sabe:\n" + "\n".join(lines),
        "citations": [f.evidence for f in facts],
        "referred_to": next(iter(people.values())),
    }


def _with_position(expert: Expert) -> str:
    # "**Ignacio Pereyra** (Gerente de Aseguramiento de Calidad (QA), Farmalog Sur)"
    details = ", ".join(part for part in (expert.position, expert.organization) if part)
    return f"**{expert.name}**" + (f" ({details})" if details else "")


NODE = NodeSpec(
    "extract_knowledge",
    "Extraer relaciones",
    "Grafo cultural y datos",
    make_extract_knowledge,
    PROMPT,
)

# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""¿La persona extraída ya existe? Score de similitud y confianza del modelo.

Antes de guardar una relación, cada persona nombrada se compara con las que ya se
conocen (el organigrama y el grafo, `known_people`):

- score = la mitad del parecido literal del nombre (`name_similarity`, sin modelo)
  y la mitad de la similitud semántica (qué tanto la frase, el puesto y la empresa
  encajan con lo que se sabe del candidato, que la evalúa el modelo);
- confianza: qué tan seguro está el modelo de que es la misma persona.

Con los dos altos es la misma persona (`same`) y se guarda con el nombre que ya
existe; en la zona del medio, si el modelo no lo descarta, `maybe` (queda para
validar); si no, `new`. Con el
mismo nombre también decide el modelo: un homónimo de otra empresa es otra persona.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from onboarding.knowledge import KnownPerson, known_people, name_similarity, same_name
from onboarding.llm import get_structured_model, load_prompt

IDENTITY_PROMPT = Path(__file__).with_name("identity_prompt.md")

# Candidatos que se le pasan al modelo: los de nombre más parecido
MIN_LITERAL = 0.5
MAX_CANDIDATES = 3
# Peso del parecido literal en el score; el resto es la similitud semántica
LITERAL_WEIGHT = 0.5
# Misma persona: score y confianza altos, y que la frase encaje con lo que se sabe
# del candidato (semántica). Dudosa: score medio.
SAME_SCORE = 0.75
SAME_CONFIDENCE = 0.7
SAME_SEMANTIC = 0.6
# Con el modelo así de seguro, alcanza aunque la frase no hable del puesto ni del
# área ("A Julián Rearte me lo presentó Ignacio Pereyra"): la semántica no hace falta
SURE_CONFIDENCE = 0.8
# Dos candidatos así de cerca, y los dos creíbles para el modelo (dos "Juan Pérez"):
# no se elige solo, queda en duda
TIE_MARGIN = 0.1
MAYBE_SCORE = 0.5
# Si el modelo está casi seguro de que no es la misma, no hay duda: es otra persona
MAYBE_CONFIDENCE = 0.3
# Mismo nombre y apellido, una sola persona que se llama así y la frase no dice otra
# organización: es ella, salvo que el modelo lo descarte
IDENTICAL_CONFIDENCE = 0.5

Decision = Literal["same", "maybe", "new"]


@dataclass(frozen=True)
class PersonMatch:
    """Con quién coincide una persona extraída, y qué tan seguro es."""

    name: str  # como apareció en el texto
    candidate: str | None  # el nombre que ya existe, si hay alguno parecido
    source: str  # "organigrama", "grafo" o "" si no hay candidato
    literal: float
    semantic: float
    score: float
    confidence: float
    decision: Decision
    candidate_id: str = ""  # el id del nodo del candidato
    # Si no es la misma pero se llama igual que alguien que ya existe, el id con que se
    # guarda para no pisarlo ("Diego Fernandez Banco Macro"); el nombre queda limpio.
    # Vacío si no choca
    save_id: str = ""


def resolve_person(
    name: str,
    evidence: str,
    position: str = "",
    organization: str = "",
    model: BaseChatModel | None = None,
) -> PersonMatch:
    """Busca a `name` entre las personas que ya se conocen. Si hay candidatos de
    nombre parecido, siempre los juzga el modelo, aunque el nombre sea idéntico: la
    frase puede decir que es otra persona ("Diego Fernandez del banco Macro" no es
    el Jefe de Compras), aunque la extracción no haya completado la empresa."""
    people = known_people()
    namesakes = [p for p in people if same_name(name, p.name)]
    namesake = bool(namesakes)
    ranked = sorted(((name_similarity(name, p.name), p) for p in people), key=lambda pair: -pair[0])
    candidates = [(lit, p) for lit, p in ranked if lit >= MIN_LITERAL][:MAX_CANDIDATES]
    if not candidates:
        return PersonMatch(name, None, "", 0.0, 0.0, 0.0, 0.0, "new")

    judged = _judge(name, evidence, position, organization, [p for _, p in candidates], model)
    scored = []
    for literal, person in candidates:
        semantic, confidence = judged.get(person.name, (0.0, 0.0))
        score = round(LITERAL_WEIGHT * literal + (1 - LITERAL_WEIGHT) * semantic, 2)
        scored.append(
            PersonMatch(
                name,
                person.name,
                person.source,
                literal,
                semantic,
                score,
                confidence,
                "new",
                person.id,
            )
        )
    best = max(scored, key=lambda m: m.score)  # el primero, si empatan
    tied = any(
        m is not best and best.score - m.score < TIE_MARGIN and m.confidence >= SAME_CONFIDENCE
        for m in scored
    )
    identical = (
        len(namesakes) == 1
        and best.candidate_id == namesakes[0].id
        and not organization
        and best.confidence >= IDENTICAL_CONFIDENCE
    )
    if identical or (
        best.score >= SAME_SCORE
        and best.confidence >= SAME_CONFIDENCE
        and (best.semantic >= SAME_SEMANTIC or best.confidence >= SURE_CONFIDENCE)
        and not tied
    ):
        decision: Decision = "same"
    elif best.score >= MAYBE_SCORE and best.confidence >= MAYBE_CONFIDENCE:
        decision = "maybe"
    else:
        decision = "new"
    # Otra persona con el mismo nombre: otro nodo, con su empresa o su puesto en el id
    qualifier = organization or position or "homonimo"
    save_id = f"{name} {qualifier}" if namesake and decision != "same" else ""
    return PersonMatch(**{**vars(best), "decision": decision, "save_id": save_id})


def _judge(
    name: str,
    evidence: str,
    position: str,
    organization: str,
    candidates: list[KnownPerson],
    model: BaseChatModel | None,
) -> dict[str, tuple[float, float]]:
    """La similitud semántica y la confianza del modelo, por candidato."""
    names = [p.name for p in candidates]
    schema = {
        "title": "misma_persona",
        "description": "Por candidato: similitud semántica y confianza de que es la misma persona.",
        "type": "object",
        "properties": {
            "candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "enum": names},
                        "semantic": {"type": "number"},
                        "confidence": {"type": "number"},
                    },
                    "required": ["name", "semantic", "confidence"],
                },
            }
        },
        "required": ["candidates"],
    }
    mention = f"<mencion>\nNombre: {name}\nFrase: {evidence}\n"
    if position:
        mention += f"Puesto: {position}\n"
    if organization:
        mention += f"Empresa: {organization}\n"
    mention += "</mencion>\n<candidatos>\n"
    for person in candidates:
        mention += f"- {person.name} · {person.position or 'puesto desconocido'}"
        mention += f" · {person.organization or 'empresa desconocida'} ({person.source})\n"
        mention += "".join(f"  - {line}\n" for line in person.known)
    mention += "</candidatos>"

    output = invoke_structured(
        model or get_structured_model(),
        schema,
        [SystemMessage(load_prompt(IDENTITY_PROMPT)), HumanMessage(mention)],
    )
    judged = {}
    # Si la salida viene rota, el candidato queda sin puntaje: como mucho, "new"
    for item in (output or {}).get("candidates", []) if isinstance(output, dict) else []:
        try:
            if item["name"] in names:  # nada de candidatos inventados
                judged[item["name"]] = (_unit(item["semantic"]), _unit(item["confidence"]))
        except (KeyError, TypeError, ValueError):
            continue
    return judged


# El razonamiento cuenta en el tope de salida. Con 1024 (el de get_chat_model),
# Haiku 5.5 por OpenRouter razona solo, sin que se lo pidan, y a veces no le queda
# lugar para el JSON: la llamada falla por largo. Subir el tope de entrada no sirve:
# a otros modelos (deepseek, qwen) OpenRouter les da un razonamiento proporcional al
# tope, y con más tope razonan más y fallan más. Por eso se reintenta solo si falla.
OUTPUT_TOKENS = 4096


def with_output_room(model: BaseChatModel) -> BaseChatModel:
    """El mismo modelo con lugar para razonar y escribir la respuesta estructurada
    (`OUTPUT_TOKENS`). Si ya tiene más (Claude directo arranca en 16000) o no tiene
    tope, queda como está. Solo para esta llamada: no cambia el modelo de los demás."""
    current = getattr(model, "max_tokens", None)
    if isinstance(current, int) and current < OUTPUT_TOKENS:
        return model.model_copy(update={"max_tokens": OUTPUT_TOKENS})
    return model


def invoke_structured(model: BaseChatModel, schema: dict, messages: list):
    """La salida estructurada (json_schema) del modelo. Si la respuesta no entra en el
    tope de salida, se repite una vez con más lugar (`with_output_room`). El error se
    reconoce por el nombre de la clase, como en ui/errors.py: sin importar el SDK."""
    try:
        return model.with_structured_output(schema, method="json_schema").invoke(messages)
    except Exception as error:
        roomier = with_output_room(model)
        if type(error).__name__ != "LengthFinishReasonError" or roomier is model:
            raise
        return roomier.with_structured_output(schema, method="json_schema").invoke(messages)


def _unit(value: float) -> float:
    # Entre 0 y 1, por si el modelo se pasa
    return round(min(1.0, max(0.0, float(value))), 2)

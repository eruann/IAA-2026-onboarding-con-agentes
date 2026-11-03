# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Extracción de relaciones desde conversación libre. Titular: rol Grafo cultural y datos."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal, get_args

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from onboarding.knowledge.rag import document_names, read_documents
from onboarding.llm import get_chat_model, load_prompt
from onboarding.paths import CORPUS_DIR

Relation = Literal["knows_about", "introduced", "belongs_to", "owns_process"]

EXTRACTION_PROMPT = Path(__file__).with_name("extraction_prompt.md")
ORG_CHART = "organigrama.md"


@lru_cache
def _org_chart() -> str:
    return (CORPUS_DIR / ORG_CHART).read_text(encoding="utf-8")


@lru_cache
def _procedures() -> str:
    # Todo el corpus menos el organigrama, que va aparte
    return read_documents(tuple(name for name in document_names() if name != ORG_CHART))


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
                },
                "required": ["subject", "relation", "object", "evidence"],
            },
        }
    },
    "required": ["triples"],
}


@dataclass(frozen=True)
# recorrido: relacion
class KnowledgeTriple:
    subject: str
    relation: Relation
    object: str
    evidence: str  # frase textual que respalda la relación


# recorrido: extraccion
def extract_triples(text: str, model: BaseChatModel | None = None) -> list[KnowledgeTriple]:
    # Sin modelo explícito, el del proyecto (regla 5). Pasar uno sirve para probar
    # con otro modelo o, en los tests, con uno de salida fija.
    model = model or get_chat_model()
    # json_schema: el proveedor restringe la salida al esquema. Con function_calling
    # los modelos chicos (qwen2.5 7B en Ollama) inventan sus propios argumentos.
    extractor = model.with_structured_output(_SCHEMA, method="json_schema")
    # El organigrama y los procedimientos van con el prompt: sin verlos, el modelo
    # no puede saber qué relaciones ya están escritas y tiene que descartar.
    system = (
        f"{load_prompt(EXTRACTION_PROMPT)}\n"
        f"<organigrama>\n{_org_chart()}\n</organigrama>\n"
        f"<procedimientos>\n{_procedures()}\n</procedimientos>"
    )
    output = extractor.invoke([SystemMessage(system), HumanMessage(text)])
    # Nada de deducir: si la frase de respaldo no está en el texto, el modelo la
    # inventó o la parafraseó, y la relación no va al grafo.
    triples = (output or {}).get("triples", [])
    return [KnowledgeTriple(**triple) for triple in triples if triple["evidence"] in text]

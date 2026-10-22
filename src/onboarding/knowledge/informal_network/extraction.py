"""Extracción de relaciones desde conversación libre. Titular: rol Grafo cultural y datos."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal, get_args

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from onboarding.agents.prompts import load_prompt

Relation = Literal["knows_about", "introduced", "belongs_to", "owns_process"]

# corpus/ está en la raíz del repo, tanto local como en Docker (/app/corpus)
ORGANIGRAMA = Path(__file__).resolve().parents[4] / "corpus" / "organigrama.md"


@lru_cache
def _organigrama() -> str:
    return ORGANIGRAMA.read_text(encoding="utf-8")


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
def extract_triples(text: str, model: BaseChatModel) -> list[KnowledgeTriple]:
    # json_schema: el proveedor restringe la salida al esquema. Con function_calling
    # los modelos chicos (qwen2.5 7B en Ollama) inventan sus propios argumentos.
    extractor = model.with_structured_output(_SCHEMA, method="json_schema")
    # El organigrama va con el prompt: sin verlo, el modelo no puede saber qué
    # relaciones ya están escritas ahí y tiene que descartar.
    system = f"{load_prompt('extract_knowledge')}\n<organigrama>\n{_organigrama()}\n</organigrama>"
    salida = extractor.invoke([SystemMessage(system), HumanMessage(text)])
    # Nada de deducir: si la frase de respaldo no está en el texto, el modelo la
    # inventó o la parafraseó, y la relación no va al grafo.
    triples = (salida or {}).get("triples", [])
    return [KnowledgeTriple(**triple) for triple in triples if triple["evidence"] in text]

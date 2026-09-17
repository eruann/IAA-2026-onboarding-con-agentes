"""Extracción de relaciones desde conversación libre. Titular: rol Grafo cultural y datos."""

from dataclasses import dataclass
from typing import Literal

Relation = Literal["knows_about", "introduced", "belongs_to", "owns_process"]


@dataclass(frozen=True)
class KnowledgeTriple:
    subject: str
    relation: Relation
    object: str
    evidence: str  # frase textual que respalda la relación


def extract_triples(text: str) -> list[KnowledgeTriple]:
    # TODO(grafo): salida estructurada del modelo (with_structured_output de
    # LangChain sobre el prompt agents/prompts/extract_knowledge.md).
    # Nada de deducir: si la frase no lo dice, no va al grafo.
    raise NotImplementedError("TODO(grafo): extracción estructurada")

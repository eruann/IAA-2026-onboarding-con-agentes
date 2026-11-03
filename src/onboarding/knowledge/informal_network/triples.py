# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Una relación del grafo: quién sabe qué, con la frase que la respalda.

La saca de una conversación el agente `extract_knowledge` (agents/extract_knowledge).
Titular: rol Grafo cultural y datos.
"""

from dataclasses import dataclass
from typing import Literal

Relation = Literal["knows_about", "introduced", "belongs_to", "owns_process"]


@dataclass(frozen=True)
# recorrido: relacion
class KnowledgeTriple:
    subject: str
    relation: Relation
    object: str
    evidence: str  # frase textual que respalda la relación

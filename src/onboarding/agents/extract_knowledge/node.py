# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Nodo de la red informal. Titular: rol Grafo cultural y datos.

Lee un texto y saca relaciones "quién sabe qué" con `extract_triples`, la función
de la knowledge layer que hace la extracción.
"""

from langchain_core.language_models import BaseChatModel

from onboarding.agents.nodes import Node
from onboarding.agents.state import OnboardingState
from onboarding.knowledge import extract_triples

RELATIONS = {
    "knows_about": "sabe de",
    "introduced": "presentó a",
    "belongs_to": "pertenece a",
    "owns_process": "es responsable de",
}


# recorrido: nodo-red-informal
def make_extract_knowledge(model: BaseChatModel) -> Node:
    def extract_knowledge(state: OnboardingState) -> dict:
        # TODO(grafo): guardar las relaciones en nodes/edges, y correr al final de
        # cada conversación (no solo cuando se elige este nodo) sin pisar la
        # respuesta que ya dio otro agente.
        triples = extract_triples(state.get("input", ""), model)
        if not triples:
            return {"output": "No encontré relaciones con respaldo en el texto.", "citations": []}
        lines = [
            f"- **{t.subject}** {RELATIONS.get(t.relation, t.relation)} **{t.object}** "
            f"(«{t.evidence}»)"
            for t in triples
        ]
        return {
            "output": f"Encontré {len(triples)} relaciones:\n\n" + "\n".join(lines),
            "citations": [t.evidence for t in triples],
        }

    return extract_knowledge

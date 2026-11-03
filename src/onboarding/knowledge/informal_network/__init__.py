# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Red informal: quién sabe de qué y a quién se consulta de verdad.

Mapea lo que el organigrama no muestra. Parte de la knowledge layer.
Titular: rol Grafo cultural y datos. Su agente y su taller están en
agents/extract_knowledge.
"""

from onboarding.knowledge.informal_network.queries import who_knows_about
from onboarding.knowledge.informal_network.triples import KnowledgeTriple, Relation

# recorrido: red-informal-interfaz
__all__ = ["KnowledgeTriple", "Relation", "who_knows_about"]

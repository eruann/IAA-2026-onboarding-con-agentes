"""Red informal: quién sabe de qué y a quién se consulta de verdad.

Mapea lo que el organigrama no muestra. Parte de la knowledge layer.
Titular: rol Grafo cultural y datos.
"""

from onboarding.knowledge.informal_network.extraction import KnowledgeTriple, extract_triples
from onboarding.knowledge.informal_network.queries import who_knows_about
from onboarding.knowledge.informal_network.workshop import WORKSHOP

# recorrido: red-informal-interfaz
__all__ = ["WORKSHOP", "KnowledgeTriple", "extract_triples", "who_knows_about"]

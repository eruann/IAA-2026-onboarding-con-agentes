# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Nodo de la red informal: quién sabe qué. Titular: rol Grafo cultural y datos."""

from onboarding.agents.extract_knowledge.node import NODE, extract_triples, make_extract_knowledge
from onboarding.agents.extract_knowledge.workshop import WORKSHOP

__all__ = ["NODE", "WORKSHOP", "extract_triples", "make_extract_knowledge"]

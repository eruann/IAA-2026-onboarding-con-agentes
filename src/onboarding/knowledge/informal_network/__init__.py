# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Red informal: quién sabe de qué y a quién se consulta de verdad.

Mapea lo que el organigrama no muestra. Parte de la knowledge layer.
Titular: rol Grafo cultural y datos. Su agente y su taller están en
agents/extract_knowledge.
"""

from onboarding.knowledge.informal_network.people import (
    KnownPerson,
    known_people,
    name_similarity,
    same_name,
)
from onboarding.knowledge.informal_network.queries import (
    Expert,
    Fact,
    person_profile,
    what_is_known_about,
    who_knows_about,
)
from onboarding.knowledge.informal_network.store import (
    Review,
    load_graph,
    pending_reviews,
    rename_person,
    review,
    save_possible_match,
    save_tool,
    save_triples,
    set_organization,
)
from onboarding.knowledge.informal_network.triples import Criticality, KnowledgeTriple, Relation

# recorrido: red-informal-interfaz
__all__ = [
    "Criticality",
    "Expert",
    "Fact",
    "KnowledgeTriple",
    "KnownPerson",
    "Review",
    "Relation",
    "known_people",
    "load_graph",
    "name_similarity",
    "pending_reviews",
    "person_profile",
    "rename_person",
    "review",
    "same_name",
    "save_possible_match",
    "save_tool",
    "save_triples",
    "set_organization",
    "what_is_known_about",
    "who_knows_about",
]

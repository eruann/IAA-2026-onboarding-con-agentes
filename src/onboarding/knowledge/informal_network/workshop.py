"""Taller del rol Grafo: la extracción y las consultas a la red informal."""

from pathlib import Path

from onboarding.knowledge.informal_network.extraction import extract_triples
from onboarding.knowledge.informal_network.queries import who_knows_about
from onboarding.workshop import Tool, Workshop

# recorrido: taller-grafo
WORKSHOP = Workshop(
    key="grafo",
    role="Grafo cultural y datos",
    agent="extract_knowledge",
    summary=(
        "Lo no escrito: quién sabe qué, más allá del organigrama. Tu nodo corre al "
        "final de cada conversación; acá probás la extracción y las consultas solas."
    ),
    tools=(
        Tool(
            extract_triples,
            "Extraer relaciones",
            "Pegá una conversación. Ej.: A Julián Rearte me lo presentó Ignacio Pereyra.",
        ),
        Tool(
            who_knows_about, "¿Quién sabe de?", "Escribí un tema: ves a quién derivaría el agente."
        ),
    ),
    guide=Path(__file__).parent / "LEEME.md",
)

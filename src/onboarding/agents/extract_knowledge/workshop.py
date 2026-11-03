# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol Grafo cultural y datos.

Solo declara: el chat con `extract_knowledge`, su agente, y las funciones del rol
que se prueban sueltas.
"""

from pathlib import Path

from onboarding.agents.extract_knowledge.node import extract_triples
from onboarding.knowledge import who_knows_about
from onboarding.workshop import Tool, Workshop

# recorrido: taller-grafo
WORKSHOP = Workshop(
    role="Grafo cultural y datos",
    intent="extract_knowledge",
    summary=(
        "Lo no escrito: quién sabe qué, más allá del organigrama. Escribile al agente "
        "una conversación y te devuelve las relaciones que encontró, con su respaldo."
    ),
    tools=(
        Tool(
            extract_triples,
            "Extraer relaciones",
            "Pegá una conversación. Ej.: A Julián Rearte me lo presentó Ignacio Pereyra.",
        ),
        Tool(who_knows_about, "¿Quién sabe de?", "Escribí un tema: a quién derivaría el agente."),
    ),
    guide=Path(__file__).parent / "LEEME.md",
    greeting=(
        "Pegame una conversación o contame a quién le consultás qué, y te muestro las "
        "relaciones que encuentro (quién sabe de qué), cada una con la frase que la respalda."
    ),
)

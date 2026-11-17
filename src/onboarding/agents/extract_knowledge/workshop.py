# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol Grafo cultural y datos.

Solo declara: el chat con `extract_knowledge`, su agente, y las pruebas. La forma de
una relación y las consultas al grafo son producto y quedan en
knowledge/informal_network/: acá solo se llaman.
"""

from pathlib import Path

# 1. Pruebas ad hoc (andamiaje): checks.py de este agente
from onboarding.agents.extract_knowledge.checks import GRAPH_PAGE, authorize

# 2. Del agente (producto): node.py de este agente
from onboarding.agents.extract_knowledge.node import extract_triples

# 3. Del código común (producto): knowledge layer, game y demás interfaces
from onboarding.knowledge import who_knows_about
from onboarding.workshop import Embed, Tool, Workshop

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
        Tool(
            who_knows_about,
            "¿Quién sabe de?",
            "Escribí un tema: a quién derivaría el agente. Con detailed apagado, solo los "
            "nombres (lo que reciben los demás agentes); prendido, la ficha con puesto, "
            "empresa, motivo (si elegís un modelo) y estado.",
        ),
        Tool(
            authorize,
            "Autorizar",
            "Sin edge_ids, Probar te lista lo pendiente (relaciones, ¿misma persona?, "
            "contradicciones). Poné uno o varios (3, 5, 7), aprobar o rechazar, y te "
            "muestra qué hizo y lo que queda. La organización, si la escribís, se guarda "
            "en quien le falte («falta» en la lista).",
        ),
    ),
    embeds=(
        Embed(
            "Ver el grafo",
            GRAPH_PAGE,
            "El grafo real (data/informal_network.json): nodos por tipo y cada relación "
            "con su #id, llena si está confirmada y rayada si está pendiente. Arrastrá "
            "los nodos y pasá el mouse por una flecha para ver la frase. Después de "
            "extraer o autorizar, tocá Recargar.",
        ),
    ),
    guide=Path(__file__).parent / "LEEME.md",
    greeting=(
        "Pegame una conversación o contame a quién le consultás qué, y te muestro las "
        "relaciones que encuentro (quién sabe de qué), cada una con la frase que la respalda."
    ),
)

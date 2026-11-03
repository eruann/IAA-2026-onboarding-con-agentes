# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol RAG y evaluación.

Solo declara: el chat con `answer_question`, su agente, y las pruebas. Las funciones
de la knowledge layer (`retrieve`, `quote_is_supported`) son producto y quedan en
knowledge/rag/: acá solo se llaman.
"""

from pathlib import Path

# 1. Pruebas ad hoc (andamiaje): checks.py de este agente
from onboarding.agents.answer_question.checks import chunk_document, evaluate_retrieval

# 2. Del agente (producto): node.py de este agente
# (ninguna)
# 3. Del código común (producto): knowledge layer, game y demás interfaces
from onboarding.knowledge import quote_is_supported, retrieve
from onboarding.workshop import Tool, Workshop

# recorrido: taller-rag
WORKSHOP = Workshop(
    role="RAG y evaluación",
    intent="answer_question",
    summary=(
        "Lo escrito: que el bot encuentre el documento y la sección que responden "
        "cada pregunta, y medirlo. Chateá con el agente de conocimiento y probá cada "
        "pieza por separado."
    ),
    tools=(
        Tool(
            retrieve,
            "Buscar en el corpus",
            "Escribí una pregunta: trae los fragmentos más parecidos, con su documento y sección.",
        ),
        Tool(
            chunk_document,
            "Ver cómo se corta un documento",
            "Elegí un documento y mirá sus fragmentos. Probá otros tamaños.",
        ),
        Tool(
            quote_is_supported,
            "Verificar una cita",
            "Pegá una cita y el texto de donde sale: dice si está textual.",
        ),
        Tool(
            evaluate_retrieval,
            "Evaluar la búsqueda",
            "Corre las preguntas de eval/rag_questions.yaml y mide recall y precisión.",
        ),
    ),
    guide=Path(__file__).parent / "LEEME.md",
)

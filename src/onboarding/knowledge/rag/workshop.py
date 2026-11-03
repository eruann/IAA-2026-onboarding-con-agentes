# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol RAG y evaluación.

Solo declara: el chat con `answer_question`, las funciones del rol que se prueban
sueltas y dos ayudas para mirar y medir (en `checks.py`).
"""

from pathlib import Path

from onboarding.knowledge.rag.checks import chunk_document, evaluate_retrieval
from onboarding.knowledge.rag.citations import quote_is_supported
from onboarding.knowledge.rag.retriever import retrieve
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

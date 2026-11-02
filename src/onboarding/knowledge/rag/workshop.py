"""Taller del rol RAG: el agente de conocimiento y la búsqueda, por separado."""

from pathlib import Path

from onboarding.knowledge.rag.chunking import chunk_text
from onboarding.knowledge.rag.evaluation import evaluate_retrieval
from onboarding.knowledge.rag.retriever import retrieve
from onboarding.workshop import Tool, Workshop

# recorrido: taller-rag
WORKSHOP = Workshop(
    key="rag",
    role="RAG y evaluación",
    agent="answer_question",
    summary=(
        "Lo escrito: que el agente responda citando la documentación. Probá la "
        "búsqueda sola, sin el modelo, para saber si un error es de búsqueda o de respuesta."
    ),
    tools=(
        Tool(retrieve, "Buscar en el corpus", "Escribí una pregunta: ves los fragmentos que trae."),
        Tool(
            evaluate_retrieval, "Evaluar la búsqueda", "Corre las preguntas de eval/ y mide recall."
        ),
        Tool(chunk_text, "Partir un texto en fragmentos", "Pegá un documento del corpus."),
    ),
    guide=Path(__file__).parent / "LEEME.md",
)

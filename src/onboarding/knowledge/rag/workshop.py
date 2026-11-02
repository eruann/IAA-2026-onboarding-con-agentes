"""Taller del rol RAG y evaluación.

Este archivo lo armó el Tech Lead para el taller: declara las pruebas y suma dos
ayudas para mirar y medir el trabajo del rol (`chunk_document` y
`evaluate_retrieval`). Lo que hace cada prueba por dentro (cómo se corta, cómo
se busca) es del rol RAG: está en `chunking.py`, `retriever.py` y compañía.
"""

from pathlib import Path
from typing import Literal

import yaml

from onboarding.knowledge.rag.chunking import DEFAULT_MAX_CHARS, DEFAULT_OVERLAP, chunk_text
from onboarding.knowledge.rag.citations import quote_is_supported
from onboarding.knowledge.rag.corpus import CORPUS, document_names
from onboarding.knowledge.rag.retriever import retrieve
from onboarding.workshop import Tool, Workshop

# Set fijo de preguntas del rol. Solo está en la imagen de desarrollo.
QUESTIONS_FILE = CORPUS.parent / "eval" / "rag_questions.yaml"

# Los documentos del corpus, para elegirlos de una lista en el taller
CorpusDocument = Literal[document_names()]


def chunk_document(
    document: CorpusDocument,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[dict]:
    """Cómo corta `chunk_text` un documento del corpus: un fragmento por fila,
    con los títulos `##` que caen adentro (si son varios, mezcla secciones)."""
    chunks = chunk_text((CORPUS / document).read_text(encoding="utf-8"), max_chars, overlap)
    return [
        {
            "fragmento": number,
            "caracteres": len(chunk),
            "títulos ## adentro": ", ".join(
                line.removeprefix("## ").strip()
                for line in chunk.splitlines()
                if line.startswith("## ")
            ),
            "texto": chunk,
        }
        for number, chunk in enumerate(chunks, start=1)
    ]


def _expected(question: dict) -> list[str]:
    expected = question.get("expected_document")
    if expected is None:
        return []
    return [expected] if isinstance(expected, str) else list(expected)


def _row(cells: tuple[str, ...]) -> str:
    """Una fila de tabla Markdown. Un "|" dentro de una celda la partiría en dos."""
    return "| " + " | ".join(str(cell).replace("|", "\\|") for cell in cells) + " |"


def evaluate_retrieval(k: int = 5) -> str:
    """Corre las preguntas de eval/rag_questions.yaml contra `retrieve` y mide si
    trae el documento correcto. Solo el retrieval: no llama al modelo."""
    if not QUESTIONS_FILE.exists():
        raise FileNotFoundError(
            f"No está {QUESTIONS_FILE}: el set de preguntas solo viene en la imagen de desarrollo."
        )
    questions = yaml.safe_load(QUESTIONS_FILE.read_text(encoding="utf-8"))
    rows = []
    hits = 0
    precisions = []
    for question in questions:
        expected = _expected(question)
        found = [chunk.document for chunk in retrieve(question["question"], k=k)]
        if not expected:
            # Sin respuesta en el corpus: no cuenta para el recall; el agente tiene
            # que derivar. Se muestra qué trajo igual.
            result = "sin respuesta en el corpus"
        else:
            relevant = sum(document in expected for document in found)
            precisions.append(relevant / len(found) if found else 0.0)
            hit = relevant > 0
            hits += hit
            result = "✅" if hit else "❌"
        cells = (
            question["id"],
            question["question"],
            ", ".join(expected) or "—",
            ", ".join(dict.fromkeys(found)) or "—",
            result,
        )
        rows.append(_row(cells))

    answerable = len(precisions)
    recall = hits / answerable if answerable else 0.0
    precision = sum(precisions) / answerable if answerable else 0.0
    return "\n".join(
        [
            f"**Recall@{k}: {hits}/{answerable} ({recall:.0%})**: preguntas en las que "
            "trajo el documento correcto entre los resultados.",
            "",
            f"**Precisión@{k}: {precision:.0%}**: de lo que trajo, cuánto era del "
            "documento correcto (promedio).",
            "",
            "La sección todavía no se mide (issue #16).",
            "",
            "| id | pregunta | documento esperado | documentos que trajo | |",
            "|---|---|---|---|---|",
            *rows,
        ]
    )


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

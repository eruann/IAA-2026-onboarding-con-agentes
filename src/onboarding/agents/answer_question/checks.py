# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Pruebas ad hoc del taller de RAG: mirar cómo se corta un documento y medir la
búsqueda contra el set fijo de preguntas. Usan la knowledge layer por su interfaz
pública y no cambian nada."""

from typing import Literal

import yaml

from onboarding.knowledge import (
    DEFAULT_MAX_CHARS,
    DEFAULT_OVERLAP,
    chunk_text,
    document_names,
    retrieve,
)
from onboarding.paths import CORPUS_DIR, EVAL_DIR
from onboarding.workshop import markdown_table

# Set fijo de preguntas del rol. Solo está en la imagen de desarrollo.
QUESTIONS_FILE = EVAL_DIR / "rag_questions.yaml"

# Los documentos del corpus, para elegirlos de una lista en el taller
CorpusDocument = Literal[document_names()]


def chunk_document(
    document: CorpusDocument,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[dict]:
    """Cómo corta `chunk_text` un documento del corpus: un fragmento por fila,
    con los títulos `##` que caen adentro (si son varios, mezcla secciones)."""
    chunks = chunk_text((CORPUS_DIR / document).read_text(encoding="utf-8"), max_chars, overlap)
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
        rows.append(cells)

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
            markdown_table(
                ("id", "pregunta", "documento esperado", "documentos que trajo", "resultado"), rows
            ),
        ]
    )

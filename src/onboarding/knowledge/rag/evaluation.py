"""Recall del retrieval contra el set fijo de eval/rag_questions.yaml.

Mide solo la búsqueda, aparte de la calidad de la respuesta (eval/README.md):
para cada pregunta con respuesta, si `retrieve` trajo alguno de los documentos
esperados entre los primeros `k`.
"""

from pathlib import Path

import yaml

from onboarding.knowledge.rag.retriever import retrieve

# eval/ está en la raíz del repo, tanto local como en Docker (/app/eval)
QUESTIONS = Path(__file__).resolve().parents[4] / "eval" / "rag_questions.yaml"


def _expected(item: dict) -> list[str]:
    documents = item.get("expected_document")
    return documents if isinstance(documents, list) else [documents]


# recorrido: evaluar-retrieval
def evaluate_retrieval(k: int = 5) -> list[dict]:
    """Una fila por pregunta: qué documento se esperaba, cuáles trajo y si acertó."""
    questions = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))
    rows = []
    for item in questions:
        expected = _expected(item)
        if expected == [None]:
            continue  # preguntas sin respuesta: se evalúan con el agente, no acá
        found = [chunk.document for chunk in retrieve(item["question"], k=k)]
        rows.append(
            {
                "id": item["id"],
                "pregunta": item["question"],
                "esperado": ", ".join(expected),
                "trajo": ", ".join(dict.fromkeys(found)),
                "acierto": any(document in found for document in expected),
            }
        )
    return rows

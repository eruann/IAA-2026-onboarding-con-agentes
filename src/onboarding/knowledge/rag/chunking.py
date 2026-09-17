"""Partido de documentos en fragmentos.

Implementación inicial a propósito simple: corta por párrafos y junta hasta
llegar al tamaño máximo. El titular de RAG la reemplaza si la evaluación muestra
que conviene otra cosa (por encabezados, por tokens, con solape).
"""

import re

DEFAULT_MAX_CHARS = 1200
DEFAULT_OVERLAP = 150


def chunk_text(
    text: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    if max_chars <= 0:
        raise ValueError("max_chars tiene que ser mayor que cero")
    if overlap >= max_chars:
        raise ValueError("overlap tiene que ser menor que max_chars")

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = current[-overlap:] + "\n\n" + paragraph if overlap else paragraph
        else:
            # Un párrafo más largo que el máximo: se corta duro.
            for start in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[start : start + max_chars])
            current = ""

    if current:
        chunks.append(current)
    return chunks

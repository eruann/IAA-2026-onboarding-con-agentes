# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Partido de documentos en fragmentos, respetando los encabezados `##`.

Corta primero por sección (cada `## Título`); dentro de cada sección, junta
párrafos hasta `max_chars` (issue #16: antes cortaba por tamaño nomás y un
fragmento podía mezclar dos secciones distintas).
"""

import re
from dataclasses import dataclass

DEFAULT_MAX_CHARS = 1200
DEFAULT_OVERLAP = 150

# Encabezado de sección: "## Título", no "#" (título del documento) ni "###".
_SECTION_HEADING = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.MULTILINE)
# Título del documento ("# ..."), para descartarlo de la primera sección.
_DOCUMENT_TITLE = re.compile(r"^#[ \t]+.*$", re.MULTILINE)


@dataclass(frozen=True)
class Chunk:
    """Un fragmento con la sección a la que pertenece."""

    section: str  # título del "##" que lo contiene; "" si es antes del primero
    text: str


# recorrido: fragmentado
def chunk_text(
    text: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    if max_chars <= 0:
        raise ValueError("max_chars tiene que ser mayor que cero")
    if overlap >= max_chars:
        raise ValueError("overlap tiene que ser menor que max_chars")

    return [
        Chunk(section, piece)
        for section, body in _split_by_section(text)
        for piece in _split_by_size(body, max_chars, overlap)
    ]


def _split_by_section(text: str) -> list[tuple[str, str]]:
    """El documento partido en (título de sección, cuerpo), por cada `##`.

    El texto antes del primer `##` queda con sección "" (vacía si solo tenía
    el título del documento, que no es contenido).
    """
    headings = list(_SECTION_HEADING.finditer(text))
    if not headings:
        return [("", text.strip())]

    sections: list[tuple[str, str]] = []
    intro = _DOCUMENT_TITLE.sub("", text[: headings[0].start()]).strip()
    if intro:
        sections.append(("", intro))

    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        sections.append((heading.group(1).strip(), text[start:end].strip()))
    return sections


def _split_by_size(text: str, max_chars: int, overlap: int) -> list[str]:
    """Junta párrafos de `text` hasta `max_chars`, con `overlap` de solape."""
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

# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Documentos del corpus enteros, para meterlos en el prompt.

Solución transitoria hasta que exista `retrieve`: así respondía el primer chat
del proyecto (PR #15). Con documentos largos gasta muchos tokens por pregunta.
"""

from onboarding.paths import CORPUS_DIR, markdown_documents


def document_names() -> tuple[str, ...]:
    """Los documentos del corpus (su ruta dentro de corpus/), sin el README que
    documenta la carpeta."""
    return tuple(path.relative_to(CORPUS_DIR).as_posix() for path in markdown_documents())


def read_documents(names: tuple[str, ...]) -> str:
    """Los documentos pedidos, cada uno entre etiquetas <documento nombre="...">."""
    return "\n".join(
        _tagged(name, (CORPUS_DIR / name).read_text(encoding="utf-8")) for name in names
    )


def _tagged(name: str, text: str) -> str:
    return f'<documento nombre="{name}">\n{text}\n</documento>'

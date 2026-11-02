"""Documentos del corpus enteros, para meterlos en el prompt.

Solución transitoria hasta que exista `retrieve`: así respondía el primer chat
del proyecto (PR #15). Con documentos largos gasta muchos tokens por pregunta.
"""

from pathlib import Path

# corpus/ está en la raíz del repo, tanto local como en Docker (/app/corpus)
CORPUS = Path(__file__).resolve().parents[4] / "corpus"


def read_documents(names: tuple[str, ...]) -> str:
    """Los documentos pedidos, cada uno entre etiquetas <documento nombre="...">."""
    return "\n".join(
        f'<documento nombre="{name}">\n{(CORPUS / name).read_text(encoding="utf-8")}\n</documento>'
        for name in names
    )

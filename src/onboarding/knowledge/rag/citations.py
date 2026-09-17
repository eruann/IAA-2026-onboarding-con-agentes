"""Guardrail contra citas inventadas.

La propuesta se compromete a que toda respuesta cite la fuente y a verificar que
lo citado exista literalmente en el corpus. Acá está esa verificación.
"""

import re
import unicodedata


def normalize(text: str) -> str:
    """Minúsculas, sin acentos y con espacios colapsados.

    Sirve para comparar citas sin que una tilde o un salto de línea las den por
    inexistentes.
    """
    without_accents = "".join(
        char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"\s+", " ", without_accents).strip().lower()


def quote_is_supported(quote: str, source_text: str, min_length: int = 15) -> bool:
    """True si `quote` aparece textualmente en `source_text`.

    Las citas muy cortas se rechazan: coinciden con cualquier cosa y no prueban
    nada.
    """
    normalized_quote = normalize(quote)
    if len(normalized_quote) < min_length:
        return False
    return normalized_quote in normalize(source_text)

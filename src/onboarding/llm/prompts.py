# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Carga de prompts.

Cada prompt vive en un `.md` al lado del código que lo usa (el `prompt.md` de
cada agente, el `extraction_prompt.md` de la extracción de relaciones), así los
cambios se revisan en el PR igual que el código y quien entiende un agente sabe
dónde está su prompt. Se cargan siempre con `load_prompt`.
"""

from functools import lru_cache
from pathlib import Path


@lru_cache
def load_prompt(path: Path) -> str:
    """El texto del prompt en `path`, por ejemplo `Path(__file__).with_name("prompt.md")`."""
    if not path.exists():
        raise FileNotFoundError(f"No existe el prompt {path}")
    return path.read_text(encoding="utf-8")

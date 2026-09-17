"""Carga de prompts.

Los prompts viven en archivos .md al lado de este módulo para que los cambios se
revisen en el PR igual que el código.
"""

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


@lru_cache
def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"No existe el prompt {name!r} en {PROMPTS_DIR}")
    return path.read_text(encoding="utf-8")

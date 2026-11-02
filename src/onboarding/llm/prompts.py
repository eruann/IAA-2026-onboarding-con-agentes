# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Carga de prompts.

Los prompts viven en `agents/prompts/*.md` para que los cambios se revisen en el
PR igual que el código. La carga está acá, junto al modelo, y no en `agents`: así
la knowledge layer también los usa (la extracción de relaciones) sin depender de
`agents`, que a su vez depende de la capa.
"""

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "agents" / "prompts"


@lru_cache
def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"No existe el prompt {name!r} en {PROMPTS_DIR}")
    return path.read_text(encoding="utf-8")

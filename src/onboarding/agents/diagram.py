# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""El lineage del grafo, para dibujarlo (ver lineage.py).

El dibujo no lee el código por su cuenta: usa la arquitectura de
`agents/grafo.json` y le suma el estado de hoy (qué sigue en TODO, quién usa qué,
chequeos de reglas). Lo arma la interfaz como diagrama de flujo (ui/grafo.js).
"""

import inspect
import json
from collections.abc import Callable
from pathlib import Path

# Lo genera `python -m onboarding.agents.lineage`
LINEAGE_FILE = Path(__file__).with_name("grafo.json")


# recorrido: dibujo-grafo
def load_lineage() -> dict:
    # Import acá y no arriba: `python -m onboarding.agents.lineage` carga este paquete
    # antes de correr lineage.py, y si el paquete ya lo importó, Python avisa.
    from onboarding.agents.lineage import current_state

    return current_state(json.loads(LINEAGE_FILE.read_text(encoding="utf-8")))


def knowledge_used_by(fn: Callable) -> list[str]:
    """Las funciones de la knowledge layer que usa `fn` (ella misma, si es una), para
    marcarlas en el dibujo cuando se corre una prueba de un taller."""
    from onboarding.agents.lineage import follow, knowledge_exports  # ver load_lineage

    exports = knowledge_exports()
    used = {name for name, export in exports.items() if export is fn}
    if inspect.isfunction(fn):  # solo se puede leer el código de una función Python
        used |= set(follow(fn, exports)["knowledge"])
    return sorted(used)

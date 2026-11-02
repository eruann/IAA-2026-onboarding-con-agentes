# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""El lineage del grafo, para dibujarlo (ver lineage.py).

El dibujo no lee el código por su cuenta: usa la arquitectura de
`agents/grafo.json` y le suma el estado de hoy (qué sigue en TODO, quién usa qué,
chequeos de reglas). Lo arma la interfaz como diagrama de flujo (ui/grafo.js).
"""

import json
from pathlib import Path

# Lo genera `python -m onboarding.agents.lineage`
LINEAGE_FILE = Path(__file__).with_name("grafo.json")


# recorrido: dibujo-grafo
def load_lineage() -> dict:
    # Import acá y no arriba: `python -m onboarding.agents.lineage` carga este paquete
    # antes de correr lineage.py, y si el paquete ya lo importó, Python avisa.
    from onboarding.agents.lineage import current_state

    return current_state(json.loads(LINEAGE_FILE.read_text(encoding="utf-8")))

# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""El lineage del grafo (`agents/grafo.json`, ver lineage.py), para dibujarlo.

El dibujo no lee el código: solo muestra lo que dice el lineage generado. Lo arma
la interfaz como diagrama de flujo (ui/grafo.js).
"""

import json
from pathlib import Path

# Lo genera `python -m onboarding.agents.lineage`
LINEAGE_FILE = Path(__file__).with_name("grafo.json")


# recorrido: dibujo-grafo
def load_lineage() -> dict:
    return json.loads(LINEAGE_FILE.read_text(encoding="utf-8"))

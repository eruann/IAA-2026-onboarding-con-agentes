# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Una relación del grafo: quién sabe qué, con la frase que la respalda.

La saca de una conversación el agente `extract_knowledge` (agents/extract_knowledge).
Titular: rol Grafo cultural y datos.
"""

from dataclasses import dataclass
from typing import Literal

Relation = Literal["knows_about", "introduced", "belongs_to", "owns_process", "works_with"]
Criticality = Literal["high", "medium", "low"]


@dataclass(frozen=True)
# recorrido: relacion
class KnowledgeTriple:
    subject: str
    relation: Relation
    object: str
    evidence: str  # frase textual que respalda la relación
    criticality: Criticality  # impacto si se pierde este conocimiento
    # Para detectar contradicciones al guardar (store.py): "Diego no se encarga
    # de X" niega una relación; "Diego es el único que..." la hace exclusiva.
    negated: bool = False
    exclusive: bool = False
    # Solo si el texto lo dice ("Julio, el vendedor de Droguería Norte"): sirve para
    # la gente de afuera, que no está en el organigrama. Vacío si no se sabe.
    subject_position: str = ""
    subject_organization: str = ""
    # De qué nodo se habla, si no alcanza con el nombre: un homónimo de otra empresa
    # ("Diego Fernandez Banco Macro") o alguien ya conocido. Vacío: sale del nombre.
    # Lo completa el agente al resolver personas, no la extracción.
    subject_id: str = ""
    object_id: str = ""
    # Que la revise una persona aunque sea de criticidad baja: por ejemplo, si no se
    # sabe de qué organización es. Lo completa el agente, no la extracción.
    needs_review: bool = False
    # Por qué conviene revisarla, para quien la revisa: por ejemplo, que la tarea no
    # encaja con el puesto oficial de la persona. Lo completa el agente.
    review_note: str = ""
    # Deducida, no dicha: la herramienta de algo que la persona hizo ("hizo la tabla
    # dinámica del informe de ventas" y el informe se hace en Excel: sabe de Excel).
    # Siempre baja y pendiente, con el motivo en `review_note`. Lo completa el agente.
    inferred: bool = False

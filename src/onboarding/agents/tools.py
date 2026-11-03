# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Herramientas que los agentes pueden llamar. Titular: rol Agentes.

Regla: una tool es una función chica con tipos claros que envuelve la interfaz
pública de otro módulo (`knowledge`, `game`). Nada de SQL acá adentro. Las firmas
son una propuesta: se pueden cambiar al implementarlas.
"""


def search_documentation(query: str, k: int = 5) -> str:
    """Los fragmentos de la documentación que responden `query`, con su fuente."""
    raise NotImplementedError("TODO(agentes): envolver knowledge.retrieve")


def who_knows(topic: str) -> str:
    """Las personas que saben de `topic`, para derivar."""
    raise NotImplementedError("TODO(agentes): envolver knowledge.who_knows_about")


def pending_missions(person_key: str) -> str:
    """Las misiones que le faltan a una persona."""
    raise NotImplementedError("TODO(agentes): envolver game.employee_board")

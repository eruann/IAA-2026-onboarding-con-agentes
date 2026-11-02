"""¿Esta función ya está implementada o sigue en TODO?

Lo usa la interfaz para mostrar en cada ficha qué falta y de quién es. Mira el
código sin ejecutarlo: nada de llamar a la base ni al modelo para averiguarlo.
"""

import ast
import inspect
import textwrap
from collections.abc import Callable


def is_pending(fn: Callable) -> bool:
    """True si el cuerpo de la función tiene un `raise NotImplementedError` directo."""
    try:
        source = textwrap.dedent(inspect.getsource(fn))
    except (OSError, TypeError):
        return False
    tree = ast.parse(source)
    function = next(
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    )
    for statement in function.body:
        if isinstance(statement, ast.Raise) and statement.exc is not None:
            raised = statement.exc.func if isinstance(statement.exc, ast.Call) else statement.exc
            if isinstance(raised, ast.Name) and raised.id == "NotImplementedError":
                return True
    return False

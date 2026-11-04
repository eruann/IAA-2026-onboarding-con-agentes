# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Lineage del grafo: qué nodos hay, cómo se conectan y qué usa cada uno.

Lee el código sin ejecutar los nodos. Tiene dos partes:

- **La arquitectura** (`build_lineage`), que se guarda en `agents/grafo.json`: el
  grafo tal como lo compila `build_graph()` (nodos y flechas), y para cada nodo la
  cadena de llamadas hasta la knowledge layer (lo que exporta `onboarding.knowledge`)
  y hasta el modelo. Cambia solo cuando cambia la arquitectura, y su diff en el PR
  lo muestra. Un test verifica que esté al día:

      docker compose run --rm app python -m onboarding.agents.lineage

- **El estado actual** (`current_state`), que no se guarda: se calcula al abrir el
  panel. Qué sigue en TODO, quién usa cada función de la capa fuera del grafo y los
  chequeos de reglas de AGENTS.md. Cambia con el trabajo de cada rol (implementar
  `retrieve`, por ejemplo), por eso no va al JSON: si fuera, el test frenaría a
  quien no tocó la arquitectura.

Es la base que dibuja la interfaz (`/ui`, botón Grafo) y la que puede leer un LLM
para entender la arquitectura o compararla con la documentación.
"""

import argparse
import ast
import copy
import inspect
import json
import sys
import textwrap
import types
import typing
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from langchain_core.language_models import BaseChatModel, FakeListChatModel
from langgraph.graph import END, START

import onboarding.knowledge as knowledge
from onboarding.agents.diagram import LINEAGE_FILE as OUTPUT
from onboarding.agents.graph import NODES, build_graph
from onboarding.paths import REPO_ROOT, repo_relative
from onboarding.workshop import is_pending

PACKAGE = REPO_ROOT / "src" / "onboarding"

# Cómo se ve cada nodo en el dibujo: el título que declara cada agente
NODE_TITLES = {node.name: node.title for node in NODES}
# Métodos que, llamados sobre el modelo, son una llamada al LLM
MODEL_METHODS = {"invoke", "ainvoke", "stream", "astream", "batch", "with_structured_output"}
# Límite de profundidad al seguir llamadas: alcanza para este código y evita ciclos
MAX_DEPTH = 6


def knowledge_exports() -> dict[str, Callable]:
    """La única puerta de la knowledge layer: sus funciones públicas."""
    return {
        name: getattr(knowledge, name)
        for name in knowledge.__all__
        if inspect.isfunction(getattr(knowledge, name))
    }


def _where(fn: Callable) -> str:
    return repo_relative(inspect.getsourcefile(fn))


def _tree(fn: Callable) -> ast.AST:
    return ast.parse(textwrap.dedent(inspect.getsource(fn)))


def _scope(fn: Callable) -> dict:
    """Los nombres que ve `fn`: los del módulo y los que captura de afuera (closure)."""
    scope = dict(fn.__globals__)
    if fn.__closure__:
        scope |= {
            name: cell.cell_contents
            for name, cell in zip(fn.__code__.co_freevars, fn.__closure__, strict=True)
        }
    return scope


def _resolve(fn: Callable, call: ast.Call) -> object | None:
    """A qué objeto apunta una llamada `f(...)` o `modulo.f(...)` dentro de `fn`."""
    scope = _scope(fn)
    target = call.func
    if isinstance(target, ast.Name):
        return scope.get(target.id)
    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
        owner = scope.get(target.value.id)
        if isinstance(owner, types.ModuleType):
            return getattr(owner, target.attr, None)
    return None


def _is_chat_model_type(hint: object) -> bool:
    if isinstance(hint, type) and issubclass(hint, BaseChatModel):
        return True
    return any(_is_chat_model_type(arg) for arg in typing.get_args(hint))


def _is_model(fn: Callable, name: str) -> bool:
    """Si `name` dentro de `fn` es un modelo: por el objeto que captura (el modelo que
    recibe un nodo) o por el tipo del parámetro (`model: BaseChatModel`)."""
    if isinstance(_scope(fn).get(name), BaseChatModel):
        return True
    try:
        hints = typing.get_type_hints(fn)
    except Exception:  # anotaciones que no se pueden resolver: no es un modelo conocido
        return False
    return name in hints and _is_chat_model_type(hints[name])


def _calls_model(fn: Callable, call: ast.Call) -> bool:
    target = call.func
    return (
        isinstance(target, ast.Attribute)
        and target.attr in MODEL_METHODS
        and isinstance(target.value, ast.Name)
        and _is_model(fn, target.value.id)
    ) or (isinstance(target, ast.Name) and target.id in ("get_chat_model", "get_structured_model"))


def _ours(obj: object) -> bool:
    return inspect.isfunction(obj) and obj.__module__.startswith("onboarding.")


def follow(fn: Callable, exports: dict[str, Callable], depth: int = 0, seen=None) -> dict:
    """Recorre las llamadas de `fn`: devuelve qué funciones de la knowledge layer usa
    (con la cadena por la que llega) y por qué cadena llega al modelo."""
    seen = seen if seen is not None else set()
    found = {"knowledge": {}, "model": None}
    if fn in seen or depth > MAX_DEPTH:
        return found
    seen.add(fn)
    by_object = {id(obj): name for name, obj in exports.items()}
    for call in (n for n in ast.walk(_tree(fn)) if isinstance(n, ast.Call)):
        if _calls_model(fn, call) and found["model"] is None:
            found["model"] = [fn.__name__]
        target = _resolve(fn, call)
        if id(target) in by_object:
            found["knowledge"].setdefault(by_object[id(target)], [fn.__name__])
            continue
        # Una función con @lru_cache (u otro decorador con functools.wraps): la de adentro
        target = inspect.unwrap(target) if callable(target) else target
        if _ours(target):
            inner = follow(target, exports, depth + 1, seen)
            for name, chain in inner["knowledge"].items():
                found["knowledge"].setdefault(name, [fn.__name__, *chain])
            if inner["model"] and found["model"] is None:
                found["model"] = [fn.__name__, *inner["model"]]
    return found


def _todos(fn: Callable) -> list[str]:
    """Los comentarios TODO de la función, cada uno con sus líneas de continuación."""
    todos: list[str] = []
    current: list[str] | None = None
    for line in inspect.getsource(fn).splitlines():
        comment = line.strip()
        if comment.startswith("# TODO("):
            current = [comment.removeprefix("# ")]
            todos.append("")
        elif current is not None and comment.startswith("#"):
            current.append(comment.removeprefix("#").strip())
        else:
            current = None
            continue
        todos[-1] = " ".join(current)
    return todos


# --- Chequeos de reglas de AGENTS.md -----------------------------------------

# Imports internos de la knowledge layer permitidos fuera de ella, con su motivo
KNOWLEDGE_EXCEPTIONS = {
    "src/onboarding/db/models.py": "registra las tablas de la capa para Alembic",
}
PROVIDER_PACKAGES = (
    "openai",
    "langchain_openai",
    "anthropic",
    "langchain_anthropic",
    "ollama",
    "langchain_ollama",
)


def _imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.lineno, node.module))
        elif isinstance(node, ast.Import):
            found += [(node.lineno, alias.name) for alias in node.names]
    return found


def _code_files() -> list[Path]:
    return sorted(p for p in PACKAGE.rglob("*.py") if not p.name.endswith("_test.py"))


def _check_knowledge_door() -> dict:
    violations = []
    for path in _code_files():
        relative = repo_relative(path)
        if relative.startswith("src/onboarding/knowledge/") or relative in KNOWLEDGE_EXCEPTIONS:
            continue
        for line, module in _imports(path):
            if module.startswith(
                ("onboarding.knowledge.rag", "onboarding.knowledge.informal_network")
            ):
                violations.append(f"{relative}:{line} importa {module}")
    return {
        "id": "puerta-knowledge",
        "regla": "AGENTS.md, regla 4: a la knowledge layer se entra solo por onboarding.knowledge",
        "ok": not violations,
        "detalle": violations,
        "excepciones": [f"{path}: {why}" for path, why in KNOWLEDGE_EXCEPTIONS.items()],
    }


def _check_model_factory() -> dict:
    violations = []
    for path in _code_files():
        relative = repo_relative(path)
        if relative.startswith("src/onboarding/llm/"):
            continue
        for line, module in _imports(path):
            if module.split(".")[0] in PROVIDER_PACKAGES:
                violations.append(f"{relative}:{line} importa {module}")
    return {
        "id": "modelo-por-get-chat-model",
        "regla": "AGENTS.md, regla 5: el modelo sale siempre de onboarding.llm.get_chat_model()",
        "ok": not violations,
        "detalle": violations,
    }


def _callers() -> dict[str, set[str]]:
    """Para cada nombre de función, los archivos que la llaman (fuera de `agents/`).

    Se cuentan llamadas, no menciones: pasar la función a un taller no es usarla.
    """
    found: dict[str, set[str]] = defaultdict(set)
    for path in _code_files():
        relative = repo_relative(path)
        if relative.startswith("src/onboarding/agents/"):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call):
                target = node.func
                called = (
                    target.id if isinstance(target, ast.Name) else getattr(target, "attr", None)
                )
                if called:
                    found[called].add(relative)
    return found


def _graph():
    return build_graph(FakeListChatModel(responses=[""])).get_graph()


# recorrido: lineage
def build_lineage() -> dict:
    """La arquitectura, lista para guardar como JSON: nodos, flechas y knowledge layer."""
    graph = _graph()
    exports = knowledge_exports()

    nodes = []
    for key, node in graph.nodes.items():
        if key in (START, END):
            continue
        fn = node.data.func
        found = follow(fn, exports)
        nodes.append(
            {
                "id": key,
                "titulo": NODE_TITLES.get(key, key),
                "archivo": _where(fn),
                "funcion": fn.__qualname__,
                "usa": [
                    {"funcion": name, "via": chain}
                    for name, chain in sorted(found["knowledge"].items())
                ],
                "modelo": {"via": found["model"]} if found["model"] else None,
            }
        )

    used = {use["funcion"] for node in nodes for use in node["usa"]}
    layer = []
    for name in sorted(exports):
        fn = exports[name]
        model = follow(fn, {})["model"]
        layer.append(
            {
                "funcion": name,
                "archivo": _where(fn),
                "usada_por_el_grafo": name in used,
                "modelo": {"via": model} if model else None,
            }
        )

    return {
        "generado_por": "python -m onboarding.agents.lineage",
        "nodos": nodes,
        "flechas": [
            {"desde": edge.source, "hasta": edge.target, "condicional": edge.conditional}
            for edge in graph.edges
        ],
        "knowledge_layer": layer,
    }


def current_state(lineage: dict) -> dict:
    """El lineage con el estado de hoy: TODOs de cada nodo, funciones pendientes,
    quién las usa fuera del grafo y chequeos de reglas. No modifica `lineage`."""
    lineage = copy.deepcopy(lineage)
    functions = {
        key: node.data.func for key, node in _graph().nodes.items() if key not in (START, END)
    }
    exports = knowledge_exports()
    callers = _callers()

    for node in lineage["nodos"]:
        node["todos"] = _todos(functions[node["id"]]) if node["id"] in functions else []
    for item in lineage["knowledge_layer"]:
        fn = exports.get(item["funcion"])
        item["pendiente"] = bool(fn) and is_pending(fn)
        item["usada_fuera_del_grafo"] = sorted(callers[item["funcion"]] - {item["archivo"]})
        item["doc"] = (inspect.getdoc(fn) or "").split("\n\n")[0] if fn else ""

    pending = [item["funcion"] for item in lineage["knowledge_layer"] if item["pendiente"]]
    lineage["chequeos"] = [
        _check_knowledge_door(),
        _check_model_factory(),
        {
            "id": "pendientes",
            "regla": "Funciones de la knowledge layer que todavía son un TODO",
            "ok": None,
            "detalle": pending,
        },
    ]
    return lineage


def render(lineage: dict) -> str:
    return json.dumps(lineage, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="no escribe: falla si el archivo no está al día"
    )
    args = parser.parse_args()
    content = render(build_lineage())
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != content:
            sys.exit(f"{OUTPUT.name} no está al día. Regeneralo con: python -m {__spec__.name}")
        print(f"{OUTPUT.name} al día")
        return
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"Escrito {repo_relative(OUTPUT)}")


if __name__ == "__main__":
    main()

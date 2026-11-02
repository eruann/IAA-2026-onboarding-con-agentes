# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Lineage del grafo: qué nodos hay, cómo se conectan y qué usa cada uno.

Genera `agents/grafo.json` leyendo el código, sin ejecutar los nodos:

- el grafo tal como lo compila `build_graph()` (nodos y flechas);
- para cada nodo, la cadena de llamadas hasta la knowledge layer (lo que exporta
  `onboarding.knowledge`) y hasta el modelo, siguiendo las funciones hacia adentro;
- qué funciones siguen en TODO, y los comentarios TODO de cada nodo;
- chequeos de reglas de AGENTS.md que se pueden verificar mirando el código.

Es la base que dibuja la interfaz (`/ui`, botón Grafo) y la que puede leer un LLM
para entender la arquitectura o compararla con la documentación. Un test verifica
que el archivo esté al día con el código:

    docker compose run --rm app python -m onboarding.agents.lineage
"""

import argparse
import ast
import inspect
import json
import sys
import textwrap
import types
from collections.abc import Callable
from pathlib import Path

from langchain_core.language_models import FakeListChatModel
from langgraph.graph import END, START

import onboarding.knowledge as knowledge
from onboarding.agents.diagram import LINEAGE_FILE as OUTPUT
from onboarding.agents.graph import build_graph
from onboarding.workshop import is_pending

PACKAGE = Path(__file__).resolve().parents[1]  # src/onboarding
ROOT = PACKAGE.parents[1]  # raíz del repo

# Cómo se ve cada nodo en el dibujo. Un nodo sin entrada se muestra con su nombre.
NODE_TITLES = {
    "answer_question": "Responder pregunta",
    "generate_quest": "Armar misión",
    "validate_evidence": "Validar evidencia",
    "extract_knowledge": "Extraer relaciones",
}
# Métodos que, llamados sobre el modelo, son una llamada al LLM
MODEL_METHODS = {"invoke", "ainvoke", "stream", "astream", "batch", "with_structured_output"}
# Límite de profundidad al seguir llamadas: alcanza para este código y evita ciclos
MAX_DEPTH = 6


def _knowledge_exports() -> dict[str, Callable]:
    """La única puerta de la knowledge layer: sus funciones públicas."""
    return {
        name: getattr(knowledge, name)
        for name in knowledge.__all__
        if inspect.isfunction(getattr(knowledge, name))
    }


def _where(fn: Callable) -> str:
    return str(Path(inspect.getsourcefile(fn)).resolve().relative_to(ROOT))


def _tree(fn: Callable) -> ast.AST:
    return ast.parse(textwrap.dedent(inspect.getsource(fn)))


def _resolve(fn: Callable, call: ast.Call) -> object | None:
    """A qué objeto apunta una llamada `f(...)` o `modulo.f(...)` dentro de `fn`."""
    scope = dict(fn.__globals__)
    if fn.__closure__:
        scope |= {
            name: cell.cell_contents
            for name, cell in zip(fn.__code__.co_freevars, fn.__closure__, strict=True)
        }
    target = call.func
    if isinstance(target, ast.Name):
        return scope.get(target.id)
    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
        owner = scope.get(target.value.id)
        if isinstance(owner, types.ModuleType):
            return getattr(owner, target.attr, None)
    return None


def _calls_model(call: ast.Call) -> bool:
    target = call.func
    return (
        isinstance(target, ast.Attribute)
        and target.attr in MODEL_METHODS
        and isinstance(target.value, ast.Name)
        and target.value.id in {"model", "extractor"}
    ) or (isinstance(target, ast.Name) and target.id == "get_chat_model")


def _ours(obj: object) -> bool:
    return inspect.isfunction(obj) and obj.__module__.startswith("onboarding.")


def _follow(fn: Callable, exports: dict[str, Callable], depth: int = 0, seen=None) -> dict:
    """Recorre las llamadas de `fn`: devuelve qué funciones de la knowledge layer usa
    (con la cadena por la que llega) y por qué cadena llega al modelo."""
    seen = seen if seen is not None else set()
    found = {"knowledge": {}, "model": None}
    if fn in seen or depth > MAX_DEPTH:
        return found
    seen.add(fn)
    by_object = {id(obj): name for name, obj in exports.items()}
    for call in (n for n in ast.walk(_tree(fn)) if isinstance(n, ast.Call)):
        if _calls_model(call) and found["model"] is None:
            found["model"] = [fn.__name__]
        target = _resolve(fn, call)
        if id(target) in by_object:
            found["knowledge"].setdefault(by_object[id(target)], [fn.__name__])
        elif _ours(target):
            inner = _follow(target, exports, depth + 1, seen)
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
        relative = str(path.relative_to(ROOT))
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
        relative = str(path.relative_to(ROOT))
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


def _callers_outside_graph(name: str, own_file: str) -> list[str]:
    """Archivos que llaman a `name` sin ser parte del grafo (p. ej. la ingesta o el seed).

    Se cuentan llamadas, no menciones: pasar la función a un taller no es usarla.
    """
    found = []
    for path in _code_files():
        relative = str(path.relative_to(ROOT))
        if relative in (own_file,) or relative.startswith("src/onboarding/agents/"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                target = node.func
                called = (
                    target.id if isinstance(target, ast.Name) else getattr(target, "attr", None)
                )
                if called == name:
                    found.append(relative)
                    break
    return found


# recorrido: lineage
def build_lineage() -> dict:
    """El lineage completo, listo para guardar como JSON."""
    graph = build_graph(FakeListChatModel(responses=[""])).get_graph()
    exports = _knowledge_exports()

    nodes = []
    for key, node in graph.nodes.items():
        if key in (START, END):
            continue
        fn = node.data.func
        found = _follow(fn, exports)
        nodes.append(
            {
                "id": key,
                "titulo": NODE_TITLES.get(key, key),
                "archivo": _where(fn),
                "funcion": fn.__qualname__,
                "todos": _todos(fn),
                "usa": [
                    {"funcion": name, "via": chain}
                    for name, chain in sorted(found["knowledge"].items())
                ],
                "modelo": {"via": found["model"]} if found["model"] else None,
            }
        )

    used = sorted({use["funcion"] for node in nodes for use in node["usa"]})
    layer = []
    for name in sorted(exports):
        fn = exports[name]
        model = _follow(fn, {})["model"]
        layer.append(
            {
                "funcion": name,
                "archivo": _where(fn),
                "pendiente": is_pending(fn),
                "usada_por_el_grafo": name in used,
                "usada_fuera_del_grafo": _callers_outside_graph(name, _where(fn)),
                "modelo": {"via": model} if model else None,
                "doc": (inspect.getdoc(fn) or "").split("\n\n")[0],
            }
        )

    pending = [item["funcion"] for item in layer if item["pendiente"]]
    return {
        "generado_por": "python -m onboarding.agents.lineage",
        "nodos": nodes,
        "flechas": [
            {"desde": edge.source, "hasta": edge.target, "condicional": edge.conditional}
            for edge in graph.edges
        ],
        "knowledge_layer": layer,
        "chequeos": [
            _check_knowledge_door(),
            _check_model_factory(),
            {
                "id": "pendientes",
                "regla": "Funciones de la knowledge layer que todavía son un TODO",
                "ok": None,
                "detalle": pending,
            },
        ],
    }


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
    print(f"Escrito {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

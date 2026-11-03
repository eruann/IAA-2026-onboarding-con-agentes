"""Cada archivo dice si es producto o andamiaje (ver "Producto y andamiaje" en AGENTS.md).

La marca va en la primera línea, para buscarla fácil (`grep -rl "^# andamiaje"`), y
debajo la leyenda completa, para que quien abra el archivo entienda la intención.

Además, el producto tiene que funcionar sin el andamiaje (ADR 0013): borrarlo es
borrar archivos, sin tocar nada más. Los dos últimos tests lo controlan, y viven
acá porque este archivo no es de ningún módulo: sobrevive al borrado.
"""

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).parent

LEGENDS = {
    "producto": (
        "Este archivo es parte del producto: el asistente de onboarding que se",
        "entrega y se evalúa.",
    ),
    "andamiaje": (
        "Este archivo es andamiaje: una ayuda para que el equipo de estudiantes",
        "construya, pruebe o entienda el producto (talleres, diagramas, guías).",
        "No es parte del producto.",
    ),
}
# Cómo empieza un comentario en cada tipo de archivo
PREFIX = {".py": "#", ".js": "//", ".md": ">"}


def _tagged_files() -> list[Path]:
    files = [*SRC.rglob("*.py"), *SRC.rglob("*.js"), *SRC.rglob("LEEME.md")]
    return sorted(
        path
        for path in files
        if not path.name.endswith("_test.py")
        and path.name != "conftest.py"
        # Las migraciones las genera Alembic: son producto, sin marca
        and "migrations/versions" not in path.as_posix()
        and "__pycache__" not in path.parts
    )


def expected_header(tag: str, suffix: str) -> list[str]:
    prefix = PREFIX[suffix]
    legend = [f"{prefix} {line}" for line in LEGENDS[tag]]
    if suffix == ".md":
        # En Markdown, en negrita y en su propio párrafo dentro de la cita
        return [f"{prefix} **{tag}**", prefix, *legend]
    return [f"{prefix} {tag}", *legend]


@pytest.mark.parametrize("path", _tagged_files(), ids=lambda path: str(path.relative_to(SRC)))
def test_cada_archivo_dice_si_es_producto_o_andamiaje(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    tag = lines[0].removeprefix(PREFIX[path.suffix]).strip(" *") if lines else ""
    options = "\n\n".join("\n".join(expected_header(t, path.suffix)) for t in LEGENDS)
    assert tag in LEGENDS, f"Falta la marca al principio de {path.name}. Copiá una:\n\n{options}"
    header = expected_header(tag, path.suffix)
    assert lines[: len(header)] == header, (
        f"La leyenda de {path.name} no coincide. Tiene que ser:\n\n" + "\n".join(header)
    )


def _tag(path: Path) -> str | None:
    """La marca de un archivo (producto o andamiaje), o None si no tiene."""
    first = path.read_text(encoding="utf-8").split("\n", 1)[0]
    tag = first.removeprefix(PREFIX.get(path.suffix, "#")).strip(" *")
    return tag if tag in LEGENDS else None


def _module_path(module: str) -> Path | None:
    """El archivo de un módulo de onboarding (onboarding.a.b), si existe."""
    parts = module.split(".")[1:]
    for candidate in (SRC.joinpath(*parts).with_suffix(".py"), SRC.joinpath(*parts, "__init__.py")):
        if parts and candidate.exists():
            return candidate
    return SRC / "__init__.py" if not parts else None


def _is_product(path: Path) -> bool:
    """Producto: un archivo con su marca, o un test del producto (el de un módulo de
    producto, o uno suelto que no es de ningún módulo, como conftest.py)."""
    if path.name.endswith("_test.py") or path.name == "conftest.py":
        module = path.with_name(path.name.removesuffix("_test.py") + ".py")
        return not module.exists() or _tag(module) == "producto"
    return _tag(path) == "producto"


def _imported_modules(path: Path) -> list[tuple[int, str]]:
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found += [(node.lineno, alias.name) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            # `from onboarding.ui import prefs` importa el módulo onboarding.ui.prefs
            found.append((node.lineno, node.module))
            found += [(node.lineno, f"{node.module}.{alias.name}") for alias in node.names]
    return [(line, module) for line, module in found if module.startswith("onboarding")]


def test_el_producto_no_importa_andamiaje() -> None:
    problems = []
    for path in sorted(SRC.rglob("*.py")):
        if "__pycache__" in path.parts or not _is_product(path):
            continue
        for line, module in _imported_modules(path):
            target = _module_path(module)
            if target and _tag(target) == "andamiaje":
                problems.append(f"{path.relative_to(SRC)}:{line} importa {module} (andamiaje)")
    assert not problems, "El producto no puede depender del andamiaje:\n" + "\n".join(problems)


def _scaffolding(path: Path) -> bool:
    if path.name in ("LEEME.md", "grafo.json"):
        return True
    return path.suffix in PREFIX and path.suffix != ".md" and _tag(path) == "andamiaje"


def test_sin_el_andamiaje_el_producto_arranca(tmp_path: Path) -> None:
    # Copia src/, borra todo lo que es andamiaje (y los tests de lo borrado) e
    # importa cada módulo que queda, incluida la app con sus pantallas
    copy = tmp_path / "src"
    shutil.copytree(SRC.parent, copy, ignore=shutil.ignore_patterns("__pycache__"))
    package = copy / SRC.name
    removed = [path for path in package.rglob("*") if path.is_file() and _scaffolding(path)]
    if not removed:
        pytest.skip("Ya no hay andamiaje: el producto es todo lo que queda")
    for path in removed:
        path.unlink()
        path.with_name(path.stem + "_test.py").unlink(missing_ok=True)
    modules = sorted(
        ".".join(path.relative_to(copy).with_suffix("").parts).removesuffix(".__init__")
        for path in package.rglob("*.py")
        if not path.name.endswith("_test.py")
        and path.name != "conftest.py"
        and "migrations" not in path.parts
    )
    script = (
        "import importlib, onboarding\n"
        "print(onboarding.__file__)\n"
        f"for name in {modules!r}:\n"
        "    importlib.import_module(name)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(copy)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "Sin el andamiaje, el producto no arranca:\n" + result.stderr
    # Que haya importado la copia y no el paquete instalado
    assert result.stdout.startswith(str(package)), result.stdout

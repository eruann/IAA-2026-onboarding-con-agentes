"""Cada archivo dice si es producto o andamiaje (ver "Producto y andamiaje" en AGENTS.md).

La marca va en la primera línea, para buscarla fácil (`grep -rl "^# andamiaje"`), y
debajo la leyenda completa, para que quien abra el archivo entienda la intención.
"""

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

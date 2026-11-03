# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Dónde está cada cosa del repo, en un solo lugar.

Sirve igual en tu compu y en Docker (donde el repo está en /app). Los tests que
necesitan otros datos parchean `DATA_DIR` acá y alcanza para todos.
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"  # personas, misiones y canje de la empresa ficticia
CORPUS_DIR = REPO_ROOT / "corpus"  # los documentos de la empresa
EVAL_DIR = REPO_ROOT / "eval"  # sets fijos de evaluación (solo en la imagen de desarrollo)


def repo_relative(path: Path | str) -> str:
    """La ruta desde la raíz del repo (src/onboarding/...), para mostrarla."""
    resolved = Path(path).resolve()
    return str(resolved.relative_to(REPO_ROOT)) if resolved.is_relative_to(REPO_ROOT) else str(path)


def load_data_yaml(name: str, required: bool = False) -> list[dict]:
    """Una lista de `data/<name>`. Si falta: lista vacía, o error si `required`."""
    path = DATA_DIR / name
    if not path.exists():
        if required:
            raise FileNotFoundError(f"No está {repo_relative(path)}.")
        logger.warning("Falta %s: se saltea", repo_relative(path))
        return []
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def markdown_documents(directory: Path | None = None) -> list[Path]:
    """Los documentos `.md` de una carpeta (por defecto el corpus), sin su README,
    que explica la carpeta y no es un documento de la empresa."""
    directory = directory or CORPUS_DIR
    return sorted(path for path in directory.glob("**/*.md") if path.name != "README.md")

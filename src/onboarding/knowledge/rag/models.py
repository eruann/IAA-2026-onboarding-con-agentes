# recorrido: tablas-rag
"""Tablas del corpus. Titular: rol RAG.

Modelo de embeddings: `bge-m3` vía Ollama (ADR 0005). Dimensión del vector:
1024 — fija por la decisión del ADR, cambiarla implica una migración nueva y
reindexar todo el corpus.

Un chunk guarda además documento y sección, porque sin eso no se puede citar la
fuente ni verificar la cita.

LIMITACIÓN CONOCIDA (a propósito, no accidental): `chunking.py` corta por
párrafos, sin conciencia de encabezados `##`. Con los documentos del corpus
actual (todos menores a 1200 caracteres), cada documento se convierte en un
único fragmento que incluye todas sus secciones juntas — por eso `section`
queda nullable: hoy no se puede poblar con precisión real. Si el corpus crece
con documentos más largos, esto se vuelve un problema real y conviene mejorar
`chunk_text` para que corte respetando encabezados.
"""

from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from onboarding.db.base import Base

EMBEDDING_DIMENSION = 1024


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    # Nombre del archivo en corpus/, ej. "compras.md".
    document: Mapped[str] = mapped_column(String(255), index=True)
    # Encabezado `##` de origen dentro del documento. Nullable: ver limitación
    # conocida arriba del archivo.
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSION))

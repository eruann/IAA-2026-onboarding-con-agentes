# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

# recorrido: tablas-rag
"""Tablas del corpus. Titular: rol RAG.

`documents` guarda un hash del contenido para que la ingesta sea idempotente:
si el archivo no cambió, no hace falta recalcular embeddings. `chunks` guarda
documento y sección, porque sin eso no se puede citar la fuente ni verificar
la cita.
"""

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from onboarding.db.base import Base
from onboarding.knowledge.rag.embeddings import EMBEDDING_DIM


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Ruta relativa a corpus/ (lo que devuelve document_names())
    path: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # sha256 del contenido: si no cambió, la ingesta lo saltea.
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (Index("ix_chunks_document_id", "document_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    # Encabezado "##" dentro del que cae el fragmento; "" si es antes del primero.
    section: Mapped[str] = mapped_column(String(300), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)

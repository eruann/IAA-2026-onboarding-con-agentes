"""Tablas del corpus. Titular: rol RAG.

TODO(rag): definir `documents` y `chunks`. La columna del vector depende del
modelo de embeddings (ADR 0005), así que la migración sale recién con esa
decisión tomada:

    from pgvector.sqlalchemy import Vector
    embedding: Mapped[list[float]] = mapped_column(Vector(DIMENSION))

Un chunk guarda además documento y sección, porque sin eso no se puede citar la
fuente ni verificar la cita.
"""

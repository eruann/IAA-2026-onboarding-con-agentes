"""Reconcilia la clave natural de people con el modelo actual.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("people")}
    if "key" not in columns:
        op.add_column("people", sa.Column("key", sa.String(length=80), nullable=True))

    # Las filas conocidas conservan las claves de data/people.yaml para que el
    # próximo seed las actualice en vez de crear personas duplicadas.
    op.execute(
        sa.text(
            """
            UPDATE people
            SET key = CASE name
                WHEN 'Ana Ruiz' THEN 'ana-ingresante'
                WHEN 'Marcela Duarte' THEN 'jefe-operaciones'
                WHEN 'Pablo Sosa' THEN 'referente-logistica'
                WHEN 'Diego Fernández' THEN 'jefe-compras'
                WHEN 'Lucía Paredes' THEN 'referente-sistemas'
                WHEN 'Romina Castro' THEN 'jefa-rrhh'
                WHEN 'Martín Ibarra' THEN 'gerente-general'
                ELSE 'legacy-person-' || id::text
            END
            WHERE key IS NULL OR key = ''
            """
        )
    )
    op.alter_column("people", "key", existing_type=sa.String(length=80), nullable=False)

    unique_constraints = inspector.get_unique_constraints("people")
    unique_columns = [tuple(constraint["column_names"]) for constraint in unique_constraints]
    if ("key",) not in unique_columns:
        op.create_unique_constraint("uq_people_key", "people", ["key"])


def downgrade() -> None:
    # `key` forma parte del esquema definido por la revisión 0003. Esta revisión
    # solo repara bases que quedaron atrás respecto de ese esquema.
    pass

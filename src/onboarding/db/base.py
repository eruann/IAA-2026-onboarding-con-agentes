from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base común de todos los modelos. Cada área define sus tablas en su propio models.py."""

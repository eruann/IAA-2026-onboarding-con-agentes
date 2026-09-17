"""Registro de modelos para Alembic.

Si tu área agrega tablas, importá acá su módulo `models` para que
`alembic revision --autogenerate` las detecte. Este es uno de los pocos
archivos compartidos: avisá en el chat antes de tocarlo.
"""

from onboarding.db.base import Base
from onboarding.game import models as game_models  # noqa: F401
from onboarding.knowledge.informal_network import models as informal_network_models  # noqa: F401
from onboarding.knowledge.rag import models as rag_models  # noqa: F401
from onboarding.llm import models as llm_models  # noqa: F401

__all__ = ["Base"]

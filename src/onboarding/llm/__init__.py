# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Acceso al modelo. Ningún otro módulo instancia un cliente por su cuenta."""

from onboarding.llm.catalog import ModelCatalog, ModelOption, model_catalog
from onboarding.llm.factory import get_chat_model
from onboarding.llm.prompts import load_prompt

__all__ = ["ModelCatalog", "ModelOption", "get_chat_model", "load_prompt", "model_catalog"]

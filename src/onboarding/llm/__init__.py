"""Acceso al modelo. Ningún otro módulo instancia un cliente por su cuenta."""

from onboarding.llm.catalog import ModelOption, available_models
from onboarding.llm.factory import get_chat_model

__all__ = ["ModelOption", "available_models", "get_chat_model"]

"""Acceso al modelo. Ningún otro módulo instancia un cliente por su cuenta."""

from onboarding.llm.factory import get_chat_model

__all__ = ["get_chat_model"]

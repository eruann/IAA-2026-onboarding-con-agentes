"""Configuración del sistema. Único lugar donde se leen variables de entorno."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["fake", "openrouter", "openai_compat"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://onboarding:onboarding@localhost:5433/onboarding"

    # Modelo. El código nunca nombra un proveedor: todo sale de llm.factory.
    llm_provider: LLMProvider = "fake"
    llm_model: str = "anthropic/claude-haiku-4.5"
    openrouter_api_key: SecretStr | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openai_compat_base_url: str = "http://ollama:11434/v1"
    openai_compat_api_key: SecretStr | None = SecretStr("ollama")

    # Slack por Events API (HTTP). No se usa Socket Mode: no hay worker aparte.
    slack_bot_token: SecretStr | None = None
    slack_signing_secret: SecretStr | None = None

    @field_validator(
        "openrouter_api_key",
        "openai_compat_api_key",
        "slack_bot_token",
        "slack_signing_secret",
        mode="before",
    )
    @classmethod
    def empty_secret_means_unset(cls, value: object) -> object:
        # Render, Docker y .env dejan las variables "vacías" como "" en vez de no
        # definirlas. Un secreto vacío tiene que valer como no configurado: si no,
        # Slack se monta con tokens vacíos y el control de "falta la key" no salta.
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        # Los proveedores gestionados entregan postgres:// o postgresql://.
        # SQLAlchemy necesita que el driver sea explícito.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value

    @property
    def slack_enabled(self) -> bool:
        return self.slack_bot_token is not None and self.slack_signing_secret is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()

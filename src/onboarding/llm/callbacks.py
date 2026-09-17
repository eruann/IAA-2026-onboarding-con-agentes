"""Registro de uso: tokens, costo y latencia de cada llamada al modelo.

La propuesta se compromete a justificar costo por ingresante con datos, así que
toda llamada queda registrada en la tabla `llm_calls`.
"""

import logging
import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from onboarding.llm.models import LLMCall

logger = logging.getLogger(__name__)


class UsageLogger(BaseCallbackHandler):
    def __init__(self, purpose: str = "unknown") -> None:
        self.purpose = purpose
        self._started_at: dict[UUID, float] = {}

    def on_llm_start(self, serialized: dict, prompts: list[str], *, run_id: UUID, **kw: Any):
        self._started_at[run_id] = time.perf_counter()

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kw: Any) -> None:
        elapsed_ms = int((time.perf_counter() - self._started_at.pop(run_id, 0)) * 1000)
        usage = (response.llm_output or {}).get("token_usage", {})
        model = (response.llm_output or {}).get("model_name", "unknown")

        call = LLMCall(
            purpose=self.purpose,
            model=model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=elapsed_ms,
        )
        logger.info(
            "llm_call purpose=%s model=%s in=%s out=%s ms=%s",
            call.purpose,
            call.model,
            call.input_tokens,
            call.output_tokens,
            call.latency_ms,
        )
        # TODO(plataforma): persistir `call` en la tabla llm_calls.
        # Se hace acá, en una sesión propia y sin romper la request si falla:
        # una llamada al modelo no puede fallar porque no se pudo escribir la métrica.

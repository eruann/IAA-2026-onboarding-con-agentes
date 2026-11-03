import asyncio
import json

import pytest

from onboarding.ui import prefs


def test_guardar_espera_a_que_el_navegador_confirme(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    async def run_javascript(code: str, timeout: float) -> bool:
        calls.append(code)
        return True

    monkeypatch.setattr(prefs.ui, "run_javascript", run_javascript)

    asyncio.run(prefs.save({"person": "ana", "prefers_dark": True}))

    # Se esperó la respuesta (si no, run_javascript nunca habría corrido)
    assert len(calls) == 1
    stored = json.dumps(json.dumps({"person": "ana"}))
    assert f'localStorage.setItem("onboarding", {stored})' in calls[0]


def test_si_el_navegador_no_responde_guardar_sigue(monkeypatch: pytest.MonkeyPatch) -> None:
    async def run_javascript(code: str, timeout: float) -> None:
        raise TimeoutError

    monkeypatch.setattr(prefs.ui, "run_javascript", run_javascript)

    asyncio.run(prefs.save({"person": "ana"}))

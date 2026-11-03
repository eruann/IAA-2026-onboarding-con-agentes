from pathlib import Path

import pytest

from onboarding.llm import load_prompt


def test_carga_el_prompt_de_un_archivo(tmp_path: Path) -> None:
    path = tmp_path / "prompt.md"
    path.write_text("Sos un agente de prueba.", encoding="utf-8")

    assert load_prompt(path) == "Sos un agente de prueba."


def test_un_prompt_que_no_existe_avisa_cual_falta(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="no-existe.md"):
        load_prompt(tmp_path / "no-existe.md")

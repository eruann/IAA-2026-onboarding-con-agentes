import pytest

from onboarding.llm import load_prompt
from onboarding.llm.prompts import PROMPTS_DIR


def test_carga_un_prompt_de_agents_prompts() -> None:
    assert PROMPTS_DIR.as_posix().endswith("src/onboarding/agents/prompts")
    assert load_prompt("answer_question") == (PROMPTS_DIR / "answer_question.md").read_text(
        encoding="utf-8"
    )


def test_un_prompt_que_no_existe_avisa_cual_falta() -> None:
    with pytest.raises(FileNotFoundError, match="no_existe"):
        load_prompt("no_existe")

import pytest

from onboarding.agents import AGENTS, CHAT_AGENTS
from onboarding.agents.prompts import PROMPTS_DIR


def test_hay_un_coordinador_y_un_nodo_final() -> None:
    assert [spec.kind for spec in AGENTS].count("router") == 1
    assert [spec.kind for spec in AGENTS].count("final") == 1


def test_las_keys_no_se_repiten() -> None:
    keys = [spec.key for spec in AGENTS]

    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("spec", AGENTS, ids=lambda spec: spec.key)
def test_cada_agente_tiene_su_carpeta_con_test(spec) -> None:
    assert spec.code_file.name == "node.py"
    assert (spec.code_file.parent / "node_test.py").exists()


@pytest.mark.parametrize("spec", CHAT_AGENTS, ids=lambda spec: spec.key)
def test_cada_agente_que_responde_tiene_su_prompt(spec) -> None:
    assert (PROMPTS_DIR / f"{spec.key}.md").exists()

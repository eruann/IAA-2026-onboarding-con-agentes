import pytest
from langchain_core.language_models import FakeListChatModel

from onboarding.agents.workshop import NODES, WORKSHOP, ask_node, show_prompt


class _ModeloQueFalla(FakeListChatModel):
    def invoke(self, *args, **kwargs):
        raise RuntimeError("el proveedor no responde")


def test_muestra_el_prompt_de_cada_nodo() -> None:
    for node in NODES:
        assert f"agents/prompts/{node}.md" in show_prompt(node)


def test_preguntarle_a_un_nodo_dice_por_donde_paso_y_cuanto_tardo(
    fake_llm: FakeListChatModel,
) -> None:
    report = ask_node("answer_question", "¿Quién es el Jefe de Tesorería?", fake_llm)

    assert report.startswith("respuesta de prueba")
    assert "Recorrido: Inicio → answer_question → Fin" in report
    assert report.endswith(" s**")


def test_si_falla_el_modelo_muestra_su_error_y_no_el_del_turno() -> None:
    with pytest.raises(RuntimeError, match="el proveedor no responde"):
        ask_node("generate_quest", "hola", _ModeloQueFalla(responses=["x"]))


def test_el_chat_ofrece_todos_los_nodos() -> None:
    assert {WORKSHOP.intent, *WORKSHOP.intents} == set(NODES)

import pytest
from langchain_core.language_models import FakeListChatModel

from onboarding.agents.workshop import (
    NODES,
    WORKSHOP,
    _contract_problems,
    ab_test,
    ask_node,
    check_nodes,
    route_message,
    show_prompt,
)


class _ModeloQueFalla(FakeListChatModel):
    def invoke(self, *args, **kwargs):
        raise RuntimeError("el proveedor no responde")


def test_el_chat_del_taller_habla_con_el_coordinador() -> None:
    assert WORKSHOP.intent is None


def test_revisa_que_cada_nodo_devuelva_lo_que_espera_el_coordinador(
    fake_llm: FakeListChatModel,
) -> None:
    # Aunque llegue un modelo (la interfaz siempre manda uno), usa el fake salvo que
    # se pida el real
    report = check_nodes(model=fake_llm)

    for node in NODES:
        assert f"| {node} |" in report
    assert "| answer_question | RAG y evaluación | ✅ |" in report
    # extract_triples necesita salida estructurada: con el fake no se puede probar
    assert "el modelo fake no sabe salida estructurada" in report
    assert "· modelo fake" in report


def test_marca_lo_que_un_nodo_devuelve_mal() -> None:
    assert _contract_problems({"output": "hola", "citations": []}) == []
    assert _contract_problems("hola") == ["devuelve str, no un dict"]
    assert _contract_problems({"output": "", "inventada": 1, "citations": "x"}) == [
        "inventada no es parte del estado",
        "falta output (texto para la persona)",
        "citations tiene que ser una lista de textos",
    ]


def test_dice_a_que_nodo_iria_un_mensaje() -> None:
    assert "**answer_question**" in route_message("¿Quién es el jefe de Compras?")


def test_ab_compara_el_coordinador_con_un_nodo_directo(fake_llm: FakeListChatModel) -> None:
    same = ab_test("answer_question", "¿Quién es el jefe de Compras?", model=fake_llm)
    other = ab_test("generate_quest", "¿Quién es el jefe de Compras?", model=fake_llm)

    assert "✅ El coordinador eligió el mismo nodo. ✅ Las respuestas son iguales." in same
    assert "⚠️ El coordinador eligió **answer_question**; vos elegiste **generate_quest**." in other


def test_ab_sin_pregunta_repite_el_ultimo_mensaje_del_chat(fake_llm: FakeListChatModel) -> None:
    history = (("user", "¿Quién es el jefe?"), ("assistant", "Diego"), ("user", "¿Y su jefa?"))

    report = ab_test("answer_question", history=history, model=fake_llm)

    assert report.startswith("Pregunta: «¿Y su jefa?» · 2 mensajes previos del chat")
    with pytest.raises(ValueError, match="mandá un mensaje en el chat"):
        ab_test("answer_question")


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

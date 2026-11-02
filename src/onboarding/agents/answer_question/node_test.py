from onboarding.agents.answer_question import make_node


def test_responde_con_el_modelo(fake_llm) -> None:
    answer_question = make_node(fake_llm)

    result = answer_question({"input": "¿cómo pido una compra?"})

    assert result["output"] == "respuesta de prueba"
    assert result["citations"] == []
    assert result["referred_to"] is None

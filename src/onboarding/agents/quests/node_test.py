from onboarding.agents.quests import make_node


def test_responde_con_el_modelo(fake_llm) -> None:
    quests = make_node(fake_llm)

    assert quests({"input": "¿qué misiones me faltan?"})["output"] == "respuesta de prueba"

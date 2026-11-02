from onboarding.agents.generate_quest import make_node


def test_responde_con_el_modelo(fake_llm) -> None:
    generate_quest = make_node(fake_llm)

    result = generate_quest({"input": "Armá misiones para un analista de Tesorería"})

    assert result["output"] == "respuesta de prueba"

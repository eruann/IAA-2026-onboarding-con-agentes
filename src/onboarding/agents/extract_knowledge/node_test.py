from onboarding.agents.extract_knowledge import make_node


def test_no_pisa_la_respuesta_del_turno(fake_llm) -> None:
    extract_knowledge = make_node(fake_llm)

    assert extract_knowledge({"input": "hola", "output": "respuesta"}) == {}

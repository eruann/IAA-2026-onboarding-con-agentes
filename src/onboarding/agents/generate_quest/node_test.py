from onboarding.agents.generate_quest import NODE, make_generate_quest


def test_propone_con_su_prompt_y_el_pedido(recording_llm) -> None:
    node = make_generate_quest(recording_llm)

    result = node({"input": "Misiones para un analista de Tesorería"})

    system, request = recording_llm.seen[0]
    assert system.content == NODE.prompt.read_text(encoding="utf-8")
    assert "Diseñás misiones de onboarding" in system.content
    assert request.content == "Misiones para un analista de Tesorería"
    assert result == {"output": "respuesta de prueba"}

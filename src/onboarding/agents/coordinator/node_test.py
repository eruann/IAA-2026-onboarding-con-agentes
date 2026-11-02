from onboarding.agents.coordinator import DEFAULT_AGENT, make_node


def test_respeta_el_agente_elegido(fake_llm) -> None:
    coordinator = make_node(fake_llm)

    assert coordinator({"agent": "quests", "input": "hola"}) == {"agent": "quests"}


def test_sin_agente_elegido_va_al_default(fake_llm) -> None:
    coordinator = make_node(fake_llm)

    assert coordinator({"input": "hola"}) == {"agent": DEFAULT_AGENT}

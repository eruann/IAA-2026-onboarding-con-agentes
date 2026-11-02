from onboarding.agents import AGENTS, graph_mermaid


def test_el_dibujo_tiene_todos_los_agentes_con_su_nombre() -> None:
    mermaid = graph_mermaid()

    assert "look: handDrawn" in mermaid
    for spec in AGENTS:
        assert spec.title in mermaid


def test_sin_recorrido_no_resalta_nada() -> None:
    assert "visited" not in graph_mermaid()


def test_el_recorrido_resalta_nodos_y_flechas() -> None:
    mermaid = graph_mermaid(["coordinator", "quests", "extract_knowledge"])

    assert "class coordinator,quests,extract_knowledge visited" in mermaid
    assert mermaid.count("linkStyle") == 4  # inicio→coord→misiones→red→fin

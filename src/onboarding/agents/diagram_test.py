from onboarding.agents.diagram import knowledge_used_by, load_lineage


def test_el_lineage_trae_lo_que_necesita_el_dibujo() -> None:
    lineage = load_lineage()

    assert {"nodos", "flechas", "knowledge_layer", "chequeos"} <= lineage.keys()
    # La arquitectura sale de grafo.json; el estado de hoy se le suma al cargar
    assert all("pendiente" in item for item in lineage["knowledge_layer"])
    ids = {node["id"] for node in lineage["nodos"]} | {"__start__", "__end__"}
    # Cada flecha une nodos que existen: si no, el dibujo queda con una línea suelta
    for edge in lineage["flechas"]:
        assert edge["desde"] in ids and edge["hasta"] in ids
    layer = {item["funcion"] for item in lineage["knowledge_layer"]}
    for node in lineage["nodos"]:
        assert {use["funcion"] for use in node["usa"]} <= layer


def test_dice_que_usa_de_la_knowledge_layer_cada_prueba() -> None:
    from onboarding.knowledge import WORKSHOPS, retrieve

    # Las pruebas del taller de RAG, por el nombre de su función
    tools = {tool.fn.__name__: tool.fn for workshop in WORKSHOPS for tool in workshop.tools}
    evaluate_retrieval, chunk_document = tools["evaluate_retrieval"], tools["chunk_document"]

    # La función misma, si es de la capa
    assert knowledge_used_by(retrieve) == ["retrieve"]
    # Una ayuda del taller que la llama por dentro
    assert knowledge_used_by(evaluate_retrieval) == ["retrieve"]
    assert knowledge_used_by(chunk_document) == ["chunk_text"]
    # Algo que no toca la capa no marca nada
    assert knowledge_used_by(lambda texto: texto.upper()) == []
    assert knowledge_used_by(len) == []
    # Una prueba que pasa por el grafo se ve en el recorrido, no en violeta
    from onboarding.agents.workshop import ask_node

    assert knowledge_used_by(ask_node) == []

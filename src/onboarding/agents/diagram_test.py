from onboarding.agents.diagram import load_lineage


def test_el_lineage_trae_lo_que_necesita_el_dibujo() -> None:
    lineage = load_lineage()

    assert {"nodos", "flechas", "knowledge_layer", "chequeos"} <= lineage.keys()
    ids = {node["id"] for node in lineage["nodos"]} | {"__start__", "__end__"}
    # Cada flecha une nodos que existen: si no, el dibujo queda con una línea suelta
    for edge in lineage["flechas"]:
        assert edge["desde"] in ids and edge["hasta"] in ids
    layer = {item["funcion"] for item in lineage["knowledge_layer"]}
    for node in lineage["nodos"]:
        assert {use["funcion"] for use in node["usa"]} <= layer

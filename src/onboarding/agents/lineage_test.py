import json

from onboarding.agents.lineage import OUTPUT, build_lineage, render


def test_grafo_json_esta_al_dia_con_el_codigo() -> None:
    # Si falla: cambiaste el grafo o lo que usan los nodos. Regeneralo con
    #   docker compose run --rm app python -m onboarding.agents.lineage
    # y commitealo: el diff muestra qué cambió en la arquitectura.
    assert OUTPUT.read_text(encoding="utf-8") == render(build_lineage())


def _node(lineage: dict, key: str) -> dict:
    return next(node for node in lineage["nodos"] if node["id"] == key)


def test_sigue_las_llamadas_hasta_el_modelo() -> None:
    answer = _node(build_lineage(), "answer_question")

    # answer_question no llama al modelo directo: lo hace _ask
    assert answer["modelo"] == {"via": ["answer_question", "_ask"]}
    assert answer["usa"] == [{"funcion": "read_documents", "via": ["answer_question"]}]


def test_la_knowledge_layer_marca_pendientes_y_uso_del_modelo() -> None:
    layer = {item["funcion"]: item for item in build_lineage()["knowledge_layer"]}

    assert layer["retrieve"]["pendiente"] is True
    assert layer["extract_triples"]["modelo"] is not None
    assert layer["read_documents"]["usada_por_el_grafo"] is True


def test_las_reglas_se_cumplen_hoy() -> None:
    checks = {check["id"]: check for check in build_lineage()["chequeos"]}

    assert checks["puerta-knowledge"]["ok"], checks["puerta-knowledge"]["detalle"]
    assert checks["modelo-por-get-chat-model"]["ok"], checks["modelo-por-get-chat-model"]["detalle"]


def test_el_json_es_valido() -> None:
    assert json.loads(OUTPUT.read_text(encoding="utf-8"))["nodos"]


def test_anota_quien_usa_cada_funcion_fuera_del_grafo() -> None:
    layer = {item["funcion"]: item for item in build_lineage()["knowledge_layer"]}

    assert "src/onboarding/seed.py" in layer["ingest_directory"]["usada_fuera_del_grafo"]
    assert "src/onboarding/knowledge/rag/ingest.py" in layer["chunk_text"]["usada_fuera_del_grafo"]
    # Existe y nadie la llama: le falta conectarla a Responder pregunta
    assert layer["quote_is_supported"]["usada_fuera_del_grafo"] == []
    assert layer["quote_is_supported"]["usada_por_el_grafo"] is False

import json

from onboarding.agents.lineage import OUTPUT, _follow, _todos, build_lineage, current_state, render

# Funciones de ejemplo: así los tests no dependen de lo que hoy tiene cada nodo, que
# cambia cuando cada rol avanza.


def knowledge_function() -> str:
    return "dato"


def _ask(model) -> str:
    return model.invoke("hola")


def node_example(model) -> str:
    # TODO(rol): primera línea
    # que sigue acá.
    data = knowledge_function()
    return _ask(model) + data


def test_grafo_json_esta_al_dia_con_el_codigo() -> None:
    # Si falla: cambiaste la arquitectura (nodos, flechas, lo que usa cada nodo o lo
    # que exporta la knowledge layer). Regeneralo con
    #   docker compose run --rm app python -m onboarding.agents.lineage
    # y commitealo: el diff muestra qué cambió.
    assert OUTPUT.read_text(encoding="utf-8") == render(build_lineage())


def test_el_json_guarda_solo_la_arquitectura() -> None:
    # Lo que cambia con el trabajo de cada rol no va al JSON (ver lineage.py)
    lineage = json.loads(OUTPUT.read_text(encoding="utf-8"))

    assert "chequeos" not in lineage
    assert all("todos" not in node for node in lineage["nodos"])
    assert all(
        "pendiente" not in item and "usada_fuera_del_grafo" not in item
        for item in lineage["knowledge_layer"]
    )


def test_sigue_las_llamadas_hasta_la_capa_y_el_modelo() -> None:
    found = _follow(node_example, {"knowledge_function": knowledge_function})

    assert found["knowledge"] == {"knowledge_function": ["node_example"]}
    # node_example no llama al modelo directo: lo hace _ask
    assert found["model"] == ["node_example", "_ask"]


def test_junta_cada_todo_con_sus_lineas_de_continuacion() -> None:
    assert _todos(node_example) == ["TODO(rol): primera línea que sigue acá."]


def test_el_estado_actual_completa_lo_que_no_guarda_el_json() -> None:
    lineage = current_state(build_lineage())

    assert {check["id"] for check in lineage["chequeos"]} == {
        "puerta-knowledge",
        "modelo-por-get-chat-model",
        "pendientes",
    }
    for item in lineage["knowledge_layer"]:
        assert isinstance(item["pendiente"], bool)
        # El archivo donde vive la función no cuenta como uso
        assert item["archivo"] not in item["usada_fuera_del_grafo"]
    layer = {item["funcion"]: item for item in lineage["knowledge_layer"]}
    assert "src/onboarding/seed.py" in layer["ingest_directory"]["usada_fuera_del_grafo"]


def test_las_reglas_se_cumplen_hoy() -> None:
    checks = {check["id"]: check for check in current_state(build_lineage())["chequeos"]}

    assert checks["puerta-knowledge"]["ok"], checks["puerta-knowledge"]["detalle"]
    assert checks["modelo-por-get-chat-model"]["ok"], checks["modelo-por-get-chat-model"]["detalle"]

"""La página del grafo se prueba sobre un grafo temporal: nada toca data/."""

from pathlib import Path

import pytest

from onboarding.agents.extract_knowledge.checks import authorize, pending
from onboarding.agents.extract_knowledge.graph_page import GRAPH_PAGE, INFERRED_COLOR, graph_data
from onboarding.knowledge import KnowledgeTriple, save_possible_match, save_triples


@pytest.fixture(autouse=True)
def grafo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "grafo.json"
    monkeypatch.setattr("onboarding.knowledge.informal_network.store.GRAPH_PATH", path)
    return path


def test_el_grafo_vacio_no_tiene_nodos() -> None:
    assert graph_data() == {"nodes": [], "edges": []}


def test_arma_nodos_y_flechas_con_su_estado() -> None:
    save_triples(
        [
            KnowledgeTriple("Ana Ruiz", "knows_about", "impuestos", "Ana sabe.", "high"),
            KnowledgeTriple("Ignacio Pereyra", "knows_about", "desvíos", "Ignacio sabe.", "low"),
        ]
    )
    save_possible_match("Diego F", "Diego Fernández", "Diego F nos llamó.", 0.7, 0.5)

    data = graph_data()

    nodos = {n["name"]: n for n in data["nodes"]}
    assert nodos["Ana Ruiz"]["type"] == "persona"
    assert nodos["impuestos"]["type"] == "tema"
    # La persona del organigrama, con su empresa
    assert nodos["Ignacio Pereyra"]["organization"] == "Farmalog Sur"
    flechas = {e["label"]: e for e in data["edges"]}
    pendiente, confirmada = flechas["#1 sabe de"], flechas["#2 sabe de"]
    assert (pendiente["status"], pendiente["line"], pendiente["criticality"]) == (
        "pendiente",
        "dashed",
        "alta",
    )
    assert (confirmada["status"], confirmada["line"]) == ("confirmada", "solid")
    assert pendiente["evidence"] == "Ana sabe."
    (duda,) = (e for e in data["edges"] if e["label"].endswith("¿misma persona?"))
    assert duda["color"] == "#f97316"


def test_las_rechazadas_solo_si_se_piden() -> None:
    save_triples([KnowledgeTriple("Ana", "knows_about", "impuestos", "Ana sabe.", "high")])
    (ana,) = (f.edge_id for f in pending())
    authorize("rechazar", str(ana))

    assert graph_data() == {"nodes": [], "edges": []}
    (rechazada,) = graph_data(include_rejected=True)["edges"]
    assert (rechazada["status"], rechazada["line"]) == ("rechazada", "dotted")


def test_la_pagina_cuelga_de_la_interfaz() -> None:
    assert GRAPH_PAGE.startswith("/ui/talleres/")


def test_la_deducida_se_distingue_y_lleva_su_motivo() -> None:
    save_triples(
        [
            KnowledgeTriple(
                "Diego",
                "knows_about",
                "Excel",
                "Diego hizo la tabla dinámica.",
                "low",
                needs_review=True,
                review_note="deducido: la tabla es de un Excel",
                inferred=True,
            )
        ]
    )

    (flecha,) = graph_data()["edges"]

    assert flecha["label"] == "#1 sabe de (deducida)"
    assert flecha["color"] == INFERRED_COLOR
    assert flecha["note"] == "deducido: la tabla es de un Excel"

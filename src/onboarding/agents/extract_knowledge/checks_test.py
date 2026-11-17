"""Las tarjetas para autorizar se prueban sobre un grafo temporal: nada toca data/."""

from pathlib import Path

import pytest

from onboarding.agents.extract_knowledge.checks import authorize, pending
from onboarding.knowledge import KnowledgeTriple, load_graph, save_possible_match, save_triples


@pytest.fixture(autouse=True)
def grafo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "grafo.json"
    monkeypatch.setattr("onboarding.knowledge.informal_network.store.GRAPH_PATH", path)
    return path


def _pendiente(subject: str, organization: str = "") -> KnowledgeTriple:
    return KnowledgeTriple(
        subject,
        "knows_about",
        "impuestos",
        f"{subject} sabe de impuestos.",
        "high",
        subject_organization=organization,
    )


def test_la_lista_dice_si_falta_la_organizacion() -> None:
    save_triples(
        [
            _pendiente("Flavio Zandoná"),
            _pendiente("Julio Cesar", "Banco Micro"),
            _pendiente("Ignacio Pereyra"),  # del organigrama
        ]
    )
    save_possible_match("Diego F", "Diego Fernández", "Diego F nos llamó.", 0.7, 0.5)

    filas = {(f.kind, f.summary): f.organization for f in pending()}

    assert filas == {
        ("Relación", "Flavio Zandoná sabe de impuestos"): "falta",
        ("Relación", "Julio Cesar sabe de impuestos"): "Banco Micro",
        ("Relación", "Ignacio Pereyra sabe de impuestos"): "Farmalog Sur",
        ("¿Misma persona?", "¿Diego F es Diego Fernández?"): "",
    }
    assert {f.criticality for f in pending()} == {"alta", ""}


def test_sin_ids_muestra_la_lista_para_elegir() -> None:
    save_triples([_pendiente("Flavio Zandoná")])
    (flavio,) = (f.edge_id for f in pending())

    lista = authorize("aprobar")

    assert lista.startswith("Pendientes (usá el `edge_id`):")
    fila = f"| {flavio} | Relación | Flavio Zandoná sabe de impuestos | «Flavio Zandoná sabe"
    assert fila in lista
    assert lista.endswith("| alta |  | falta |")
    assert [f.edge_id for f in pending()] == [flavio]  # no decidió nada


def test_autoriza_varios_y_muestra_lo_que_queda() -> None:
    save_triples([_pendiente("Flavio Zandoná"), _pendiente("Ana"), _pendiente("Beto")])
    flavio, ana, beto = (f.edge_id for f in pending())

    resultado = authorize("aprobar", f"{flavio}, {ana}")

    hizo, queda = resultado.split("\n\n", 1)
    assert hizo == f"**Relación #{flavio} aprobada. Relación #{ana} aprobada.**"
    assert f"| {beto} | Relación | Beto sabe de impuestos |" in queda
    assert [f.edge_id for f in pending()] == [beto]
    assert authorize("rechazar", str(beto)) == (
        f"**Relación #{beto} rechazada.**\n\nNo hay nada pendiente de revisar."
    )


def test_la_organizacion_se_guarda_aunque_se_rechace() -> None:
    save_triples([_pendiente("Flavio Zandoná"), _pendiente("Julio Cesar", "Banco Micro")])
    flavio, julio = (f.edge_id for f in pending())

    resultado = authorize("rechazar", f"{flavio} {julio}", "Farmalog Sur")

    # Solo a quien le faltaba: Julio Cesar ya era del Banco Micro
    assert "Guardé la organización de 1 persona.**" in resultado
    nodos = {n["id"]: n.get("attributes", {}) for n in load_graph()["nodes"]}
    assert nodos["flavio-zandona"]["organization"] == "Farmalog Sur"
    assert nodos["julio-cesar"]["organization"] == "Banco Micro"


def test_un_id_que_no_esta_no_frena_a_los_demas() -> None:
    save_triples([_pendiente("Ana")])
    (ana,) = (f.edge_id for f in pending())

    assert authorize("aprobar", f"99, {ana}") == (
        f"**No hay nada pendiente de revisar con el id 99. Relación #{ana} aprobada.**"
        "\n\nNo hay nada pendiente de revisar."
    )

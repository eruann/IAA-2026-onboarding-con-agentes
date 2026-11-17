"""Candidatos y parecido de nombres: sin modelo, sobre un grafo temporal."""

from pathlib import Path

import pytest

from onboarding.knowledge.informal_network.people import (
    known_people,
    name_similarity,
    same_name,
)
from onboarding.knowledge.informal_network.store import save_triples
from onboarding.knowledge.informal_network.triples import KnowledgeTriple


@pytest.fixture
def grafo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "grafo.json"
    monkeypatch.setattr("onboarding.knowledge.informal_network.store.GRAPH_PATH", path)
    return path


def test_apellidos_de_mas_o_tildes_no_bajan_el_parecido() -> None:
    assert name_similarity("Diego Fernandez Lopez Monier", "Diego Fernández") == 1.0
    assert name_similarity("julian rearte", "Julián Rearte") == 1.0


def test_un_error_de_tipeo_cuenta_como_el_mismo_nombre() -> None:
    assert name_similarity("Gerardo Gorosita", "Gerardo Gorosito") == 1.0
    assert name_similarity("Ignacio Pereira", "Ignacio Pereyra") == 1.0


def test_un_solo_nombre_o_apellido_es_ambiguo() -> None:
    assert name_similarity("Diego", "Diego Fernández") == 0.6
    assert name_similarity("Gorosito", "Sergio Gorosito") == 0.6


def test_nombres_distintos_no_se_parecen_aunque_suenen_parecido() -> None:
    assert name_similarity("Julio Cesar", "Julián Rearte") == 0.0
    assert name_similarity("Beto", "Ana Ruiz") == 0.0
    assert name_similarity("Diego Fernando Washington Sarlanga", "Diego Fernández") == 0.5


def test_mismo_nombre_es_identico_no_contenido() -> None:
    assert same_name("julian rearte", "Julián Rearte")
    assert not same_name("Diego Fernandez Lopez Monier", "Diego Fernández")
    assert not same_name("", "")


def test_conocidos_junta_organigrama_y_grafo(grafo: Path) -> None:
    save_triples(
        [
            KnowledgeTriple(
                "Julio Cesar",
                "knows_about",
                "cuenta en el Banco Macro",
                "Julio Cesar maneja nuestra cuenta en el Banco Macro.",
                "high",
                subject_organization="Banco Macro",
            ),
            KnowledgeTriple(
                "Julián Rearte",
                "knows_about",
                "desvíos",
                "Julián Rearte sabe de desvíos.",
                "low",
            ),
        ],
        grafo,
    )

    people = {p.name: p for p in known_people()}

    assert people["Julio Cesar"].source == "grafo"
    assert people["Julio Cesar"].organization == "Banco Macro"
    assert people["Diego Fernández"].position == "Jefe de Compras"
    # Está en los dos: gana el organigrama, con lo que se sabe del grafo
    rearte = people["Julián Rearte"]
    assert (rearte.source, rearte.position) == ("organigrama", "Analista de QA Sr.")
    assert rearte.known == ("knows_about desvíos («Julián Rearte sabe de desvíos.»)",)
    assert len([p for p in people.values() if p.name == "Julián Rearte"]) == 1


def test_del_organigrama_queda_el_nombre_mas_completo_y_el_puesto_oficial(grafo: Path) -> None:
    save_triples(
        [
            KnowledgeTriple(
                "Diego Fernandez Lopez Monier",
                "knows_about",
                "compras grandes",
                "Diego Fernandez Lopez Monier autoriza las compras grandes.",
                "low",
                subject_id="diego-fernandez",
            )
        ],
        grafo,
    )

    diego = next(p for p in known_people() if p.id == "diego-fernandez")

    assert (diego.name, diego.position, diego.source) == (
        "Diego Fernandez Lopez Monier",
        "Jefe de Compras",
        "organigrama",
    )

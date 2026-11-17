"""El grafo en JSON se prueba sobre un archivo temporal: nada toca data/."""

from pathlib import Path

import pytest

from onboarding.knowledge.informal_network.store import (
    CONFIRMED,
    PENDING,
    REJECTED,
    SaveReport,
    load_graph,
    pending_reviews,
    rename_person,
    review,
    save_possible_match,
    save_tool,
    save_triples,
    set_organization,
)
from onboarding.knowledge.informal_network.triples import KnowledgeTriple


def _triple(
    subject: str = "Diego",
    object: str = "compra de lápices",
    evidence: str = "Diego se encarga de la compra de lápices.",
    criticality: str = "medium",
    negated: bool = False,
    exclusive: bool = False,
) -> KnowledgeTriple:
    return KnowledgeTriple(
        subject=subject,
        relation="owns_process",
        object=object,
        evidence=evidence,
        criticality=criticality,
        negated=negated,
        exclusive=exclusive,
    )


def _edges(path: Path, relation: str = "owns_process") -> list[dict]:
    return [e for e in load_graph(path)["edges"] if e["relation"] == relation]


def test_sin_archivo_el_grafo_esta_vacio(tmp_path: Path) -> None:
    assert load_graph(tmp_path / "grafo.json") == {"nodes": [], "edges": []}


def test_relacion_nueva_se_guarda_con_sus_nodos(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"

    report = save_triples([_triple()], path)

    assert report.added == 1
    graph = load_graph(path)
    assert {(n["id"], n["type"]) for n in graph["nodes"]} == {
        ("diego", "person"),
        ("compra-de-lapices", "process"),
    }
    [edge] = graph["edges"]
    assert (edge["source"], edge["target"], edge["criticality"]) == (
        "diego",
        "compra-de-lapices",
        "medium",
    )


def test_el_estado_inicial_sale_de_la_criticidad(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"

    save_triples(
        [
            _triple(subject="Ana", criticality="low"),
            _triple(subject="Beto", criticality="medium"),
            _triple(subject="Caro", criticality="high"),
        ],
        path,
    )

    estados = {e["source"]: e["status"] for e in _edges(path)}
    assert estados == {"ana": CONFIRMED, "beto": PENDING, "caro": PENDING}


def test_relacion_repetida_no_hace_nada(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple()], path)

    # Misma relación, escrita distinto: sin tilde y con mayúscula
    report = save_triples([_triple(object="Compra de lapices")], path)

    assert (report.added, report.unchanged) == (0, 1)
    assert len(_edges(path)) == 1


def test_relacion_compatible_se_agrega(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple()], path)

    report = save_triples([_triple(object="compra de resmas")], path)

    assert report.added == 1
    assert len(_edges(path)) == 2


def test_baja_que_pide_revision_queda_pendiente(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    sin_revision = _triple(criticality="low")
    a_revisar = KnowledgeTriple(
        "Joaquín", "knows_about", "útiles", "Joaquín ve los útiles.", "low", needs_review=True
    )

    save_triples([sin_revision, a_revisar], path)

    edges = load_graph(path)["edges"]
    estados = {e["source"]: (e["status"], e["criticality"]) for e in edges}
    assert estados == {"diego": (CONFIRMED, "low"), "joaquin": (PENDING, "low")}


def test_negacion_pasa_a_pendiente_y_guarda_la_frase(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple(criticality="low")], path)  # entra confirmada
    negacion = "Diego no se encarga de la compra de lápices."

    report = save_triples([_triple(evidence=negacion, negated=True)], path)

    assert report.status_changed == 1
    [edge] = _edges(path)
    assert edge["status"] == PENDING
    assert [h["evidence"] for h in edge["history"]] == [negacion]


def test_negacion_sin_relacion_previa_no_se_guarda(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"

    report = save_triples([_triple(negated=True)], path)

    assert report.ignored == 1
    assert load_graph(path) == {"nodes": [], "edges": []}


def test_dos_exclusivas_quedan_pendientes_y_unidas_por_un_conflicto(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    diego = "Diego es el único que se encarga de la compra de lápices."
    javier = "Javier es el único que se encarga de la compra de lápices."
    save_triples([_triple(evidence=diego, criticality="low", exclusive=True)], path)

    report = save_triples([_triple(subject="Javier", evidence=javier, exclusive=True)], path)

    assert (report.added, report.conflicts) == (1, 1)
    assert {e["source"]: e["status"] for e in _edges(path)} == {
        "diego": PENDING,
        "javier": PENDING,
    }
    graph = load_graph(path)
    [conflicto] = [n for n in graph["nodes"] if n["type"] == "conflict"]
    assert conflicto["attributes"]["evidence"] == [diego, javier]
    assert {e["target"] for e in _edges(path, "contradicts")} == {"diego", "javier"}


def test_sin_exclusividad_dos_responsables_no_son_conflicto(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple()], path)

    report = save_triples([_triple(subject="Javier")], path)

    assert report.conflicts == 0
    assert _edges(path, "contradicts") == []


def test_devuelve_el_estado_final_de_cada_relacion(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple(criticality="low")], path)

    report = save_triples(
        [
            _triple(criticality="low"),  # repetida: conserva su estado
            _triple(object="compra de resmas", criticality="high"),
            _triple(object="compra de toner", negated=True),  # no estaba: no se guarda
        ],
        path,
    )

    assert report.statuses == [CONFIRMED, PENDING, None]


def test_un_conflicto_posterior_cambia_el_estado_de_una_anterior(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"

    report = save_triples(
        [
            _triple(criticality="low", exclusive=True),
            _triple(subject="Javier", criticality="low", exclusive=True),
        ],
        path,
    )

    assert report.statuses == [PENDING, PENDING]


def test_el_resumen_cuenta_lo_que_paso() -> None:
    assert SaveReport(added=2, unchanged=1, conflicts=1).summary() == (
        "2 nuevas, 1 ya estaba, 1 conflicto"
    )
    assert SaveReport().summary() == "nada para guardar"


def test_puesto_y_empresa_dichos_se_guardan_en_el_nodo_de_la_persona(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    julio = KnowledgeTriple(
        subject="Julio Gómez",
        relation="knows_about",
        object="faltantes de insulina",
        evidence="Julio Gómez, el vendedor de Droguería Norte, sabe de faltantes de insulina.",
        criticality="low",
        subject_position="vendedor",
        subject_organization="Droguería Norte",
    )

    save_triples([_triple(), julio], path)

    nodes = {n["id"]: n for n in load_graph(path)["nodes"]}
    assert nodes["julio-gomez"]["attributes"] == {
        "position": "vendedor",
        "organization": "Droguería Norte",
    }
    # Si la frase no dice nada, el nodo no lleva atributos vacíos
    assert "attributes" not in nodes["diego"]


def test_un_puesto_dicho_despues_actualiza_el_nodo(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple()], path)

    # La misma relación, ahora con el puesto: no se repite, pero el puesto se guarda
    save_triples([KnowledgeTriple(**{**vars(_triple()), "subject_position": "comprador"})], path)

    diego = next(n for n in load_graph(path)["nodes"] if n["id"] == "diego")
    assert diego["attributes"] == {"position": "comprador"}
    assert len(_edges(path)) == 1


def test_una_duda_de_identidad_queda_como_arista_pendiente_con_peso(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple(subject="Diego Sarlanga")], path)

    edge = save_possible_match(
        "Diego Sarlanga", "Diego Fernández", "Me llamó Diego Sarlanga.", 0.62, 0.4, path
    )

    assert (edge["source"], edge["relation"], edge["target"]) == (
        "diego-sarlanga",
        "may_be_same",
        "diego-fernandez",
    )
    assert (edge["status"], edge["weight"], edge["confidence"]) == (PENDING, 0.62, 0.4)
    # El candidato no estaba en el grafo (viene del organigrama): se crea su nodo
    nodes = {n["id"]: n for n in load_graph(path)["nodes"]}
    assert nodes["diego-fernandez"] == {
        "id": "diego-fernandez",
        "type": "person",
        "name": "Diego Fernández",
    }


def test_la_misma_duda_no_se_duplica_y_queda_el_peso_mayor(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_possible_match("Diego Sarlanga", "Diego Washington", "Primera frase.", 0.6, 0.5, path)
    save_possible_match("Diego Washington", "Diego Sarlanga", "Segunda frase.", 0.7, 0.6, path)
    save_possible_match("Diego Sarlanga", "Diego Washington", "Tercera frase.", 0.5, 0.9, path)

    (edge,) = _edges(path, "may_be_same")
    assert (edge["evidence"], edge["weight"], edge["confidence"]) == ("Primera frase.", 0.7, 0.6)
    assert [h["evidence"] for h in edge["history"]] == ["Segunda frase.", "Tercera frase."]


def test_renombrar_cambia_el_nombre_y_no_el_id(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple(subject="Diego Hamilton")], path)
    edges = load_graph(path)["edges"]

    assert rename_person("diego-hamilton", "Diego Fernandes Hamilton", path)

    graph = load_graph(path)
    assert [(n["id"], n["name"]) for n in graph["nodes"] if n["type"] == "person"] == [
        ("diego-hamilton", "Diego Fernandes Hamilton")
    ]
    assert graph["edges"] == edges


def test_renombrar_solo_personas_que_estan(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple(subject="Diego Hamilton")], path)

    assert not rename_person("nadie", "Alguien", path)
    # Un tema no es una persona
    assert not rename_person("compra-de-lapices", "compra de lápices y gomas", path)
    assert {n["name"] for n in load_graph(path)["nodes"]} == {
        "Diego Hamilton",
        "compra de lápices",
    }


def test_un_homonimo_con_id_propio_no_pisa_al_otro(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple(subject="Diego Fernández")], path)
    banquero = KnowledgeTriple(
        "Diego Fernandez",
        "knows_about",
        "cheques",
        "Diego Fernandez del banco Macro.",
        "high",
        subject_organization="Banco Macro",
        subject_id="Diego Fernandez Banco Macro",
    )

    save_triples([banquero], path)
    save_possible_match(
        "Diego Fernandez",
        "Diego Fernández",
        "Diego Fernandez del banco Macro.",
        0.6,
        0.4,
        path,
        name_id="diego-fernandez-banco-macro",
        candidate_id="diego-fernandez",
    )

    graph = load_graph(path)
    people = [(n["id"], n["name"]) for n in graph["nodes"] if n["type"] == "person"]
    assert people == [
        ("diego-fernandez", "Diego Fernández"),
        ("diego-fernandez-banco-macro", "Diego Fernandez"),
    ]
    assert [(e["source"], e["relation"], e["target"]) for e in graph["edges"][1:]] == [
        ("diego-fernandez-banco-macro", "knows_about", "cheques"),
        ("diego-fernandez-banco-macro", "may_be_same", "diego-fernandez"),
    ]


def test_lo_pendiente_se_lista_para_revisar(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple(), _triple("Ana", "impuestos", "Ana sabe de impuestos.", "low")], path)
    save_possible_match("Diego F", "Diego Fernández", "Diego F nos llamó.", 0.7, 0.5, path)

    reviews = pending_reviews(path)

    # La de criticidad baja entró confirmada: no está
    assert [(r.kind, r.summary) for r in reviews] == [
        ("relation", "Diego es responsable de compra de lápices"),
        ("same_person", "¿Diego F es Diego Fernández?"),
    ]
    assert reviews[0].criticality == "medium"
    assert reviews[1].detail == "score 0,70 · confianza 0,50"


def test_aprobar_y_rechazar_una_relacion(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples(
        [_triple(), _triple("Ana", evidence="Ana se encarga de la compra de lápices.")], path
    )
    diego, ana = _edges(path)

    assert review(diego["id"], approve=True, path=path) == f"Relación #{diego['id']} aprobada."
    review(ana["id"], approve=False, path=path)

    assert [e["status"] for e in _edges(path)] == [CONFIRMED, REJECTED]
    assert _edges(path)[1]["history"][-1]["evidence"] == "revisión: rechazada"
    assert pending_reviews(path) == []
    # Ya revisada: no hay nada que revisar con ese id
    with pytest.raises(ValueError, match="No hay nada pendiente"):
        review(diego["id"], approve=True, path=path)


def test_lo_rechazado_no_se_vuelve_a_proponer(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple()], path)
    review(_edges(path)[0]["id"], approve=False, path=path)

    save_triples([_triple(), _triple(negated=True)], path)

    assert [e["status"] for e in _edges(path)] == [REJECTED]


def test_aprobar_una_contradiccion_rechaza_la_otra_y_cierra_el_conflicto(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples(
        [
            _triple(exclusive=True),
            _triple("Ana", evidence="Solo Ana se encarga de la compra de lápices.", exclusive=True),
        ],
        path,
    )
    diego, ana = _edges(path)
    assert [(r.kind, r.detail) for r in pending_reviews(path)] == [
        ("conflict", f"choca con #{ana['id']}"),
        ("conflict", f"choca con #{diego['id']}"),
    ]

    message = review(ana["id"], approve=True, path=path)

    assert message == f"Relación #{ana['id']} aprobada. Rechacé la que chocaba: #{diego['id']}."
    assert [e["status"] for e in _edges(path)] == [REJECTED, CONFIRMED]
    graph = load_graph(path)
    assert not [n for n in graph["nodes"] if n["type"] == "conflict"]
    assert _edges(path, "contradicts") == []


def test_rechazar_una_contradiccion_deja_la_otra_pendiente(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples(
        [
            _triple(exclusive=True),
            _triple("Ana", evidence="Solo Ana se encarga de la compra de lápices.", exclusive=True),
        ],
        path,
    )
    diego, ana = _edges(path)

    review(diego["id"], approve=False, path=path)

    assert [(r.edge_id, r.kind) for r in pending_reviews(path)] == [(ana["id"], "relation")]


def test_aprobar_la_misma_persona_une_los_nodos(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    banquero = KnowledgeTriple(
        "Diego Fernandes Hamilton",
        "knows_about",
        "cheques",
        "Diego Fernandes Hamilton, del Banco Micro, sabe de cheques.",
        "low",
        subject_organization="Banco Micro",
    )
    save_triples([_triple("Diego Fernandez"), banquero], path)
    duda = save_possible_match("Diego Fernandes Hamilton", "Diego Fernandez", "…", 0.7, 0.6, path)

    message = review(duda["id"], approve=True, path=path)

    assert (
        message == "Unifiqué a Diego Fernandes Hamilton con Diego Fernandez: 1 relaciones movidas."
    )
    graph = load_graph(path)
    people = [n for n in graph["nodes"] if n["type"] == "person"]
    # Queda un nodo, con el id que ya existía, el nombre más completo y la empresa
    assert people == [
        {
            "id": "diego-fernandez",
            "type": "person",
            "name": "Diego Fernandes Hamilton",
            "attributes": {"organization": "Banco Micro"},
        }
    ]
    assert {e["source"] for e in graph["edges"]} == {"diego-fernandez"}
    assert _edges(path, "may_be_same") == []


def test_al_unir_una_relacion_repetida_queda_una_con_el_mejor_estado(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples(
        [
            _triple("Diego F", criticality="medium"),  # pendiente
            _triple("Diego Fernandez", criticality="low"),  # confirmada
        ],
        path,
    )
    duda = save_possible_match("Diego F", "Diego Fernandez", "…", 0.7, 0.6, path)

    review(duda["id"], approve=True, path=path)

    (unica,) = _edges(path)
    assert (unica["source"], unica["status"]) == ("diego-fernandez", CONFIRMED)


def test_rechazar_la_misma_persona_no_vuelve_a_preguntar(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    duda = save_possible_match("Diego F", "Diego Fernández", "Diego F nos llamó.", 0.7, 0.5, path)

    message = review(duda["id"], approve=False, path=path)
    save_possible_match("Diego F", "Diego Fernández", "Otra vez Diego F.", 0.8, 0.6, path)

    assert message == "Diego F y Diego Fernández son personas distintas: no se vuelve a preguntar."
    assert [e["status"] for e in _edges(path, "may_be_same")] == [REJECTED]
    assert pending_reviews(path) == []


def test_la_organizacion_que_dice_quien_revisa_queda_en_la_persona(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_triple("Flavio Zandoná")], path)

    assert set_organization("Flavio Zandoná", " Farmalog Sur ", path)
    assert not set_organization("Flavio Zandoná", "", path)  # vacía: no pisa
    assert not set_organization("Nadie", "Farmalog Sur", path)

    (flavio,) = [n for n in load_graph(path)["nodes"] if n["id"] == "flavio-zandona"]
    assert flavio["attributes"] == {"organization": "Farmalog Sur"}
    assert pending_reviews(path)[0].organization == "Farmalog Sur"


def test_la_nota_de_revision_llega_a_la_tarjeta(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    nota = "no coincide con su puesto (Gerente de Calidad): la cobranza es de Tesorería"
    triple = KnowledgeTriple(
        "Ignacio Pereyra",
        "owns_process",
        "cobranza",
        "Ignacio Pereyra se encarga de la cobranza.",
        "low",
        needs_review=True,
        review_note=nota,
    )

    save_triples([triple], path)

    (pendiente,) = pending_reviews(path)
    assert (pendiente.kind, pendiente.detail) == ("relation", nota)


def _trabaja_con(subject: str, object: str) -> KnowledgeTriple:
    return KnowledgeTriple(
        subject=subject,
        relation="works_with",
        object=object,
        evidence=f"{subject} trabaja con {object}.",
        criticality="low",
    )


def test_trabaja_con_une_a_dos_personas_y_la_inversa_no_se_duplica(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"

    save_triples([_trabaja_con("Ana Ruiz", "Pablo Sosa")], path)
    report = save_triples([_trabaja_con("Pablo Sosa", "Ana Ruiz")], path)

    assert report.added == 0 and report.unchanged == 1
    graph = load_graph(path)
    assert {(n["id"], n["type"]) for n in graph["nodes"]} == {
        ("ana-ruiz", "person"),
        ("pablo-sosa", "person"),
    }
    assert [(e["source"], e["target"]) for e in _edges(path, "works_with")] == [
        ("ana-ruiz", "pablo-sosa")
    ]


def _sabe_excel(evidence: str, inferred: bool, criticality: str = "low") -> KnowledgeTriple:
    return KnowledgeTriple(
        subject="Diego",
        relation="knows_about",
        object="Excel",
        evidence=evidence,
        criticality=criticality,
        needs_review=inferred,
        review_note="deducido: hizo la tabla dinámica" if inferred else "",
        inferred=inferred,
    )


def test_la_deducida_se_guarda_pendiente_y_marcada(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"

    save_triples([_sabe_excel("Diego hizo la tabla dinámica del informe.", True)], path)

    (edge,) = _edges(path, "knows_about")
    assert edge["inferred"] is True
    assert edge["status"] == PENDING  # baja, pero pide revisión
    assert edge["review_note"] == "deducido: hizo la tabla dinámica"


def test_lo_dicho_le_gana_a_lo_deducido(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_sabe_excel("Diego hizo la tabla dinámica del informe.", True)], path)

    report = save_triples([_sabe_excel("Diego sabe de Excel.", False)], path)

    assert report.added == 0 and report.status_changed == 1
    (edge,) = _edges(path, "knows_about")
    assert "inferred" not in edge and "review_note" not in edge
    assert edge["evidence"] == "Diego sabe de Excel."
    assert edge["status"] == CONFIRMED  # dicha y baja: entra confirmada


def test_lo_deducido_no_toca_lo_dicho(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_sabe_excel("Diego sabe de Excel.", False)], path)

    report = save_triples([_sabe_excel("Diego hizo la tabla dinámica del informe.", True)], path)

    assert report.unchanged == 1
    (edge,) = _edges(path, "knows_about")
    assert "inferred" not in edge and edge["evidence"] == "Diego sabe de Excel."


def _se_encarga(subject: str, thing: str, status_low: bool = True) -> KnowledgeTriple:
    return KnowledgeTriple(
        subject=subject,
        relation="owns_process",
        object=thing,
        evidence=f"{subject} se encarga del {thing}.",
        criticality="low" if status_low else "medium",
    )


SUPERSET = "El tablero de Gestión es de Superset."


def test_la_herramienta_de_algo_que_alguien_ya_hace_se_deduce(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_se_encarga("Santiago Sosa", "tablero de Gestión")], path)

    (deducida,) = save_tool("tableros de gestion", "Superset", SUPERSET, path)

    assert (deducida.subject, deducida.relation, deducida.object) == (
        "Santiago Sosa",
        "knows_about",
        "Superset",
    )
    assert deducida.inferred and deducida.needs_review and deducida.criticality == "low"
    assert deducida.evidence == SUPERSET and deducida.subject_id == "santiago-sosa"
    assert deducida.review_note == (
        "deducido: es responsable de tablero de Gestión (#1), y tablero de Gestión se hace "
        f"con Superset («{SUPERSET}»)"
    )
    # El dato queda en el nodo de la cosa
    nodo = next(n for n in load_graph(path)["nodes"] if n["id"] == "tablero-de-gestion")
    assert nodo["attributes"] == {"tool": "Superset", "tool_evidence": SUPERSET}


def test_si_la_herramienta_se_dijo_antes_se_deduce_al_guardar(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    assert save_tool("tablero de Gestión", "Superset", SUPERSET, path) == []  # nadie aún

    report = save_triples([_se_encarga("Santiago Sosa", "tablero de Gestión")], path)

    (deducida,) = report.deduced
    assert (deducida.subject, deducida.object, deducida.inferred) == (
        "Santiago Sosa",
        "Superset",
        True,
    )
    (edge,) = _edges(path, "knows_about")
    assert edge["inferred"] is True and edge["status"] == PENDING
    assert report.statuses == [CONFIRMED]  # la dicha, como siempre


def test_lo_rechazado_no_deduce_herramientas(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_se_encarga("Santiago Sosa", "tablero de Gestión", status_low=False)], path)
    (edge,) = _edges(path)
    review(edge["id"], approve=False, path=path)

    assert save_tool("tablero de Gestión", "Superset", SUPERSET, path) == []


def test_otra_cosa_con_palabras_parecidas_no_toma_la_herramienta(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_se_encarga("Santiago Sosa", "tablero de Compras")], path)

    assert save_tool("tablero de Gestión", "Superset", SUPERSET, path) == []


def test_un_error_de_tipeo_de_una_letra_igual_encuentra_la_cosa(tmp_path: Path) -> None:
    path = tmp_path / "grafo.json"
    save_triples([_se_encarga("Santiago Sosa", "tablero de Gestión")], path)
    con_tipeo = "el tablero de gestió está realizado en Superset"

    (deducida,) = save_tool("tablero de gestió", "Superset", con_tipeo, path)

    assert (deducida.subject, deducida.object) == ("Santiago Sosa", "Superset")
    # Se anota en el nodo que ya estaba: no nace uno nuevo con el tipeo
    assert "tablero-de-gestio" not in {n["id"] for n in load_graph(path)["nodes"]}
    # Dos letras de diferencia ya es otra cosa
    assert save_tool("tablero de gesti", "Superset", con_tipeo, path) == []

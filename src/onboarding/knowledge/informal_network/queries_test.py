"""La consulta se prueba sobre un grafo temporal, armado con save_triples."""

from pathlib import Path

import pytest

from onboarding.knowledge.informal_network.queries import (
    Expert,
    Fact,
    person_profile,
    related_topics,
    what_is_known_about,
    who_knows_about,
)
from onboarding.knowledge.informal_network.store import load_graph, review, save_triples
from onboarding.knowledge.informal_network.triples import KnowledgeTriple
from onboarding.paths import CORPUS_DIR


@pytest.fixture
def grafo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "grafo.json"
    monkeypatch.setattr("onboarding.knowledge.informal_network.store.GRAPH_PATH", path)
    return path


def _triple(
    subject: str, object: str, relation: str = "knows_about", criticality: str = "low"
) -> KnowledgeTriple:
    return KnowledgeTriple(
        subject=subject,
        relation=relation,
        object=object,
        evidence=f"{subject} y {object}.",
        criticality=criticality,
    )


def _names(topic: str, **kwargs) -> list[str]:
    return [expert.name for expert in who_knows_about(topic, **kwargs, detailed=True)]


def test_encuentra_sin_importar_plural_tildes_ni_mayusculas(grafo: Path) -> None:
    save_triples([_triple("Sergio Quinteros", "impuestos"), _triple("Ana", "Tesorería")], grafo)

    assert _names("Impuesto") == ["Sergio Quinteros"]
    assert _names("tesoreria") == ["Ana"]


def test_las_confirmadas_van_antes_que_las_pendientes(grafo: Path) -> None:
    save_triples(
        [
            _triple("Beto", "impuestos", criticality="high"),  # entra pendiente
            _triple("Caro", "impuestos"),  # entra confirmada
        ],
        grafo,
    )

    assert _names("impuestos") == ["Caro", "Beto"]


def test_con_el_mismo_estado_gana_quien_tiene_mas_relaciones(grafo: Path) -> None:
    save_triples(
        [
            _triple("Ana", "impuestos"),
            _triple("Beto", "impuestos"),
            _triple("Beto", "impuestos provinciales"),
        ],
        grafo,
    )

    assert _names("impuestos") == ["Beto", "Ana"]


def test_respeta_el_limite(grafo: Path) -> None:
    save_triples([_triple(name, "impuestos") for name in ("Ana", "Beto", "Caro", "Dani")], grafo)

    assert _names("impuestos", limit=2) == ["Ana", "Beto"]


def test_cuenta_procesos_pero_no_presentaciones(grafo: Path) -> None:
    save_triples(
        [
            _triple("Sergio", "recuperación del backup", relation="owns_process"),
            _triple("Ana", "Backup", relation="introduced"),
        ],
        grafo,
    )

    assert _names("backup") == ["Sergio"]


def test_sin_coincidencias_ni_temas_cercanos_devuelve_lista_vacia(
    grafo: Path, structured_llm
) -> None:
    nada_cerca = structured_llm({"topics": []})
    assert _names("impuestos", model=nada_cerca) == []

    save_triples([_triple("Ana", "impuestos")], grafo)

    assert _names("cámaras frías", model=nada_cerca) == []
    assert _names("de la", model=nada_cerca) == []


def test_las_palabras_de_la_pregunta_no_cuentan_como_tema(grafo: Path) -> None:
    save_triples([_triple("Joaquín", "impuestos")], grafo)

    assert _names("¿Quién es el que más sabe de impuestos?") == ["Joaquín"]


def test_sin_coincidencia_busca_en_los_temas_cercanos(grafo: Path, structured_llm) -> None:
    save_triples([_triple("Joaquín", "impuestos"), _triple("Ana", "compras")], grafo)
    modelo = structured_llm({"topics": ["impuestos"]})

    assert what_is_known_about("liquidación de IVA", model=modelo) == [
        Fact(
            "Joaquín",
            "knows_about",
            "impuestos",
            "Joaquín y impuestos.",
            True,
            nearby=True,
            person_id="joaquin",
        )
    ]
    assert _names("liquidación de IVA", model=modelo) == ["Joaquín"]
    # El modelo elige entre los temas del grafo
    related_topics("liquidación de IVA", modelo)
    assert "- impuestos\n- compras" in modelo.seen[0].content


def test_con_coincidencia_por_palabras_no_busca_temas_cercanos(
    grafo: Path, structured_llm, monkeypatch: pytest.MonkeyPatch
) -> None:
    save_triples([_triple("Joaquín", "impuestos")], grafo)

    def no_se_llama(*args, **kwargs):
        raise AssertionError("no tenía que buscar temas cercanos")

    monkeypatch.setattr("onboarding.knowledge.informal_network.queries.related_topics", no_se_llama)

    assert _names("impuestos", model=structured_llm({"people": ["joaquin"]})) == ["Joaquín"]


def test_un_tema_cercano_que_no_esta_en_el_grafo_se_descarta(grafo: Path, structured_llm) -> None:
    save_triples([_triple("Joaquín", "impuestos")], grafo)

    assert related_topics("IVA", structured_llm({"topics": ["IVA", "impuestos"]})) == ["impuestos"]
    assert related_topics("IVA", structured_llm({"topics": ["IVA"]})) == []


def test_con_el_grafo_vacio_no_se_llama_al_modelo(grafo: Path, structured_llm) -> None:
    modelo = structured_llm({"topics": ["impuestos"]})

    assert related_topics("IVA", modelo) == []
    assert modelo.seen == []


def test_lo_que_se_sabe_trae_la_frase_en_el_mismo_orden(grafo: Path) -> None:
    save_triples(
        [
            _triple("Beto", "impuestos", criticality="high"),
            _triple("Caro", "impuestos"),
        ],
        grafo,
    )

    assert what_is_known_about("impuestos") == [
        Fact("Caro", "knows_about", "impuestos", "Caro y impuestos.", True, person_id="caro"),
        Fact("Beto", "knows_about", "impuestos", "Beto y impuestos.", False, person_id="beto"),
    ]


def test_dos_homonimos_son_dos_expertos_con_su_empresa(grafo: Path) -> None:
    banquero = KnowledgeTriple(
        "Diego Fernández",
        "knows_about",
        "cheques",
        "Diego Fernández del Banco Macro sabe de cheques.",
        "low",
        subject_organization="Banco Macro",
        subject_id="Diego Fernandez Banco Macro",
    )
    save_triples([_triple("Diego Fernández", "cheques"), banquero], grafo)

    assert who_knows_about("cheques", detailed=True) == [
        Expert(
            "Diego Fernández", "Jefe de Compras", "Farmalog Sur", internal=True, status="confirmada"
        ),
        Expert("Diego Fernández", "", "Banco Macro", internal=False, status="confirmada"),
    ]


def test_la_gente_de_la_empresa_trae_el_puesto_del_organigrama(grafo: Path) -> None:
    save_triples([_triple("Ignacio Pereyra", "desvíos de calidad")], grafo)

    assert who_knows_about("desvíos", detailed=True) == [
        Expert(
            "Ignacio Pereyra",
            "Gerente de Aseguramiento de Calidad (QA)",
            "Farmalog Sur",
            True,
            status="confirmada",
        )
    ]


def test_el_puesto_se_lee_de_las_distintas_formas_del_organigrama(grafo: Path) -> None:
    # "es el ... y reporta", en una lista "Nombre, Puesto;", y "lleva ..."
    assert person_profile("julian rearte").position == "Analista de QA Sr."
    assert person_profile("Rocío Miranda").position == "Jefa de Control de Calidad y Validaciones"
    assert person_profile("Silvina Ortega").position == "A cargo de Compras y Administración"
    assert person_profile("Martín Beltrán").position == "Director Técnico suplente"


def test_todos_los_referentes_del_organigrama_tienen_puesto(grafo: Path) -> None:
    # La tabla de referentes nombra a gente que el texto tiene que haber presentado
    text = (CORPUS_DIR / "organigrama.md").read_text(encoding="utf-8")
    rows = [line.split("|") for line in text.splitlines() if line.startswith("| ")][1:]
    names = {cell.strip() for row in rows for cell in row[2:4] if cell.strip() not in {"", "—"}}

    assert names
    assert [name for name in sorted(names) if not person_profile(name).internal] == []


def test_la_gente_de_afuera_trae_lo_que_dijo_la_conversacion(grafo: Path) -> None:
    julio = KnowledgeTriple(
        subject="Julio Gómez",
        relation="knows_about",
        object="faltantes de insulina",
        evidence="Julio Gómez, el vendedor de Droguería Norte, sabe de faltantes de insulina.",
        criticality="low",
        subject_position="vendedor",
        subject_organization="Droguería Norte",
    )
    save_triples([julio, _triple("Beto", "faltantes de insulina")], grafo)

    assert who_knows_about("insulina", detailed=True) == [
        Expert("Beto", "", "", internal=False, status="confirmada"),
        Expert("Julio Gómez", "vendedor", "Droguería Norte", internal=False, status="confirmada"),
    ]


def _banqueros(grafo: Path) -> None:
    # Los dos tienen "banco" en un tema y nada confirmado: por respaldo, Ariel primero
    save_triples(
        [
            KnowledgeTriple(
                "Ariel Boldrini",
                "knows_about",
                "descuento de cheques en el banco",
                "Ariel Boldrini se encarga del descuento de cheques en el banco.",
                "medium",
            ),
            KnowledgeTriple(
                "Diego Hamilton",
                "knows_about",
                "problemas con cheques en el banco",
                "Diego Hamilton nos llamó del Banco Micro por los cheques.",
                "high",
                subject_organization="Banco Micro",
            ),
            KnowledgeTriple(
                "Diego Hamilton",
                "knows_about",
                "costos financieros",
                "Con Diego Hamilton hablamos de los costos financieros.",
                "medium",
            ),
        ],
        grafo,
    )


PREGUNTA = "¿quién es el oficial de cuentas del banco micro?"


def test_sin_modelo_ordena_por_respaldo(grafo: Path) -> None:
    _banqueros(grafo)

    assert _names(PREGUNTA) == ["Ariel Boldrini", "Diego Hamilton"]


def test_con_modelo_primero_quien_mejor_encaja(grafo: Path, structured_llm) -> None:
    _banqueros(grafo)
    modelo = structured_llm({"people": ["diego-hamilton", "ariel-boldrini"]})

    assert _names(PREGUNTA, model=modelo) == ["Diego Hamilton", "Ariel Boldrini"]
    # Ve todo lo que se sabe de cada uno, no solo lo que coincidió, y su empresa
    personas = modelo.seen[0].content
    assert "- diego-hamilton: Diego Hamilton (Banco Micro)" in personas
    assert "knows_about costos financieros" in personas
    assert modelo.seen[1].content == PREGUNTA


def test_cada_persona_trae_el_motivo_del_modelo(grafo: Path, structured_llm) -> None:
    _banqueros(grafo)
    motivo = "No figura como oficial de cuentas; se acerca por su perfil comercial."
    modelo = structured_llm(
        {
            "people": [
                {"id": "diego-hamilton", "reason": motivo},
                {"id": "ariel-boldrini", "reason": "Solo descuenta cheques."},
            ]
        }
    )

    assert who_knows_about(PREGUNTA, model=modelo, detailed=True) == [
        Expert("Diego Hamilton", "", "Banco Micro", False, reason=motivo, status="pendiente"),
        Expert(
            "Ariel Boldrini", "", "", False, reason="Solo descuenta cheques.", status="pendiente"
        ),
    ]
    # Sin modelo no hay motivo
    assert {e.reason for e in who_knows_about(PREGUNTA, detailed=True)} == {""}


def test_a_quien_el_modelo_no_nombra_queda_afuera(grafo: Path, structured_llm) -> None:
    _banqueros(grafo)
    for salida in ({"people": ["diego-hamilton"]}, {"people": ["inventado", "diego-hamilton"]}):
        assert _names(PREGUNTA, model=structured_llm(salida)) == ["Diego Hamilton"]


def test_si_nadie_encaja_no_deriva_a_nadie(grafo: Path, structured_llm) -> None:
    _banqueros(grafo)
    modelo = structured_llm({"people": []})

    assert _names("¿quién es el maestranza del banco micro?", model=modelo) == []
    assert what_is_known_about("maestranza del banco micro", model=modelo) == []


def test_una_salida_rota_deja_el_orden_por_respaldo(grafo: Path, structured_llm) -> None:
    _banqueros(grafo)
    for salida in (None, {"people": "roto"}, {"topics": []}):
        assert _names(PREGUNTA, model=structured_llm(salida)) == [
            "Ariel Boldrini",
            "Diego Hamilton",
        ]


def test_con_una_sola_persona_el_modelo_igual_la_juzga(grafo: Path, structured_llm) -> None:
    save_triples([_triple("Joaquín", "impuestos")], grafo)

    assert _names("impuestos", model=structured_llm({"people": ["joaquin"]})) == ["Joaquín"]
    assert _names("impuestos", model=structured_llm({"people": []})) == []


def test_cada_persona_trae_si_sus_relaciones_estan_confirmadas(grafo: Path) -> None:
    save_triples(
        [
            _triple("Ana", "impuestos"),  # baja: entra confirmada
            _triple("Beto", "impuestos", criticality="high"),  # entra pendiente
            _triple("Caro", "impuestos"),
            _triple("Caro", "impuestos provinciales", criticality="high"),
        ],
        grafo,
    )

    estados = {e.name: e.status for e in who_knows_about("impuestos", detailed=True)}

    assert estados == {"Ana": "confirmada", "Beto": "pendiente", "Caro": "1 de 2 confirmadas"}


def test_lo_rechazado_no_aparece(grafo: Path) -> None:
    save_triples([_triple("Ana", "impuestos"), _triple("Beto", "impuestos", criticality="high")])
    (beto,) = [e for e in load_graph()["edges"] if e["source"] == "beto"]

    review(beto["id"], approve=False)

    assert _names("impuestos") == ["Ana"]


def test_por_defecto_devuelve_solo_los_nombres_en_el_mismo_orden(grafo: Path) -> None:
    # Lo acordado con los demás roles: RAG deriva con people[0], que es un nombre
    save_triples([_triple("Ana", "impuestos"), _triple("Beto", "impuestos")], grafo)

    nombres = who_knows_about("impuestos")

    assert nombres == [e.name for e in who_knows_about("impuestos", detailed=True)]
    assert all(isinstance(nombre, str) for nombre in nombres) and nombres

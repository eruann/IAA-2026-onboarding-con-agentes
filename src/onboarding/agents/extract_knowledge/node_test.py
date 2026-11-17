"""El nodo y la extracción se prueban con un modelo de salida fija: sin red y
determinístico.

Lo que se testea acá es lo que hace el código alrededor del modelo (el filtro de
evidencia, el contexto que recibe y cómo arma la respuesta), no la calidad de la
extracción. Eso se mide en eval/.
"""

from pathlib import Path

import pytest
from langchain_core.messages import SystemMessage

from onboarding.agents.common import Models
from onboarding.agents.extract_knowledge import extract_triples, make_extract_knowledge
from onboarding.agents.extract_knowledge.node import (
    _SCHEMA,
    EXTRACTION_PROMPT,
    _review_if_unplaced,
)
from onboarding.knowledge import KnowledgeTriple, load_graph, save_triples
from onboarding.llm import load_prompt

TEXTO = "Para Excel avanzado, preguntale a Diego. Es un genio."
RESPALDO = "Para Excel avanzado, preguntale a Diego."


@pytest.fixture(autouse=True)
def grafo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # El nodo guarda en el grafo: que escriba en un archivo temporal, no en data/
    path = tmp_path / "grafo.json"
    monkeypatch.setattr("onboarding.knowledge.informal_network.store.GRAPH_PATH", path)
    return path


def _triple(evidence: str) -> dict:
    return {
        "subject": "Diego",
        "relation": "knows_about",
        "object": "Excel avanzado",
        "evidence": evidence,
        "criticality": "medium",
    }


def test_relacion_con_evidencia_textual_se_devuelve(structured_llm) -> None:
    modelo = structured_llm({"triples": [_triple(RESPALDO)]})

    triples = extract_triples(TEXTO, modelo)

    assert triples == [
        KnowledgeTriple(
            subject="Diego",
            relation="knows_about",
            object="Excel avanzado",
            evidence=RESPALDO,
            criticality="medium",
        )
    ]


def test_el_esquema_exige_criticidad_negacion_y_exclusividad() -> None:
    item = _SCHEMA["properties"]["triples"]["items"]

    assert {"criticality", "negated", "exclusive"} <= set(item["required"])
    assert {"subject_position", "subject_organization"} <= set(item["required"])
    assert item["properties"]["criticality"]["enum"] == ["high", "medium", "low"]


def test_el_sujeto_recupera_los_apellidos_que_el_modelo_recorto(structured_llm) -> None:
    texto = "Nos llamó del Banco Diego Fernandez Halmitón debido a un cheque rechazado."
    recortado = {**_triple(texto), "subject": "Diego Fernández"}

    (triple,) = extract_triples(texto, structured_llm({"triples": [recortado]}))

    assert triple.subject == "Diego Fernandez Halmitón"
    # Una coma o una minúscula cortan: no se suman palabras de más
    texto = "Para Excel avanzado, preguntale a Diego. Es un genio."
    (triple,) = extract_triples(texto, structured_llm({"triples": [_triple(RESPALDO)]}))
    assert triple.subject == "Diego"


def test_relacion_con_evidencia_inventada_se_descarta(structured_llm) -> None:
    modelo = structured_llm({"triples": [_triple("Diego sabe mucho de Excel.")]})

    assert extract_triples(TEXTO, modelo) == []


def test_salida_vacia_del_modelo_devuelve_lista_vacia(structured_llm) -> None:
    assert extract_triples(TEXTO, structured_llm(None)) == []
    assert extract_triples(TEXTO, structured_llm({"triples": []})) == []


def test_el_prompt_lleva_organigrama_y_procedimientos(structured_llm) -> None:
    modelo = structured_llm(None)

    extract_triples(TEXTO, modelo)

    system = modelo.seen[0]
    assert isinstance(system, SystemMessage)
    assert "<organigrama>" in system.content
    assert "<procedimientos>" in system.content
    assert '<documento nombre="compras.md">' in system.content
    assert '<documento nombre="README.md">' not in system.content
    assert '<documento nombre="organigrama.md">' not in system.content


def _procedimientos(texto: str, structured_llm) -> str:
    modelo = structured_llm(None)
    extract_triples(texto, modelo)
    # El último: el prompt también nombra la etiqueta
    return modelo.seen[0].content.split("<procedimientos>")[-1]


def test_el_grep_manda_solo_los_procedimientos_que_nombran_la_conversacion(
    structured_llm,
) -> None:
    texto = "Ignacio Pereyra llama a los clientes con atraso para gestionar los pagos"

    procedimientos = _procedimientos(texto, structured_llm)

    assert '<documento nombre="tesoreria.md">' in procedimientos
    assert '<documento nombre="bienvenida.md">' in procedimientos  # la criticidad sale de ahí
    assert '<documento nombre="compras.md">' not in procedimientos
    assert '<documento nombre="organigrama.md">' not in procedimientos


def test_si_el_grep_no_encuentra_nada_manda_todos_los_procedimientos(structured_llm) -> None:
    procedimientos = _procedimientos("Juan sabe tocar la guitarra", structured_llm)

    assert '<documento nombre="compras.md">' in procedimientos
    assert '<documento nombre="tesoreria.md">' in procedimientos
    assert '<documento nombre="organigrama.md">' not in procedimientos
    assert '<documento nombre="README.md">' not in procedimientos


def test_sin_modelo_usa_el_del_proyecto(monkeypatch: pytest.MonkeyPatch, structured_llm) -> None:
    modelo = structured_llm({"triples": [_triple(RESPALDO)]})
    node_module = "onboarding.agents.extract_knowledge.node"
    monkeypatch.setattr(f"{node_module}.get_structured_model", lambda: modelo)

    assert len(extract_triples(TEXTO)) == 1


class _PorEsquema:
    """Salida fija según el esquema que se pide: la extracción ("extraccion") y la
    resolución de personas ("misma_persona") esperan cosas distintas, y el
    structured_llm del conftest devuelve siempre lo mismo. No conversa."""

    def __init__(self, outputs: dict) -> None:
        self.outputs = outputs
        self.seen: dict[str, list] = {}

    def with_structured_output(self, schema: dict, method: str):
        title, model = schema["title"], self

        class _Output:
            def invoke(self, messages: list):
                model.seen[title] = messages
                return model.outputs.get(title)

        return _Output()

    def invoke(self, messages: list):
        raise AssertionError("el agente no conversa: no llama al modelo principal")


def test_el_nodo_devuelve_solo_las_relaciones_sin_conversar(grafo: Path) -> None:
    modelo = _PorEsquema({"extraccion": {"triples": [_triple(RESPALDO)]}})
    node = make_extract_knowledge(Models.same(modelo))

    result = node({"input": TEXTO, "actor_name": "Ana"})

    assert result == {
        "output": "Encontré 1 relaciones:\n\n"
        f"- **Diego** sabe de **Excel avanzado** («{RESPALDO}») · criticidad media · "
        "pendiente\n\nEn el grafo: 1 nueva.",
        "citations": [RESPALDO],
    }
    # El modelo principal no se llama (_PorEsquema falla si se lo llama). La
    # extracción usó sus instrucciones
    assert modelo.seen["extraccion"][0].content.startswith(load_prompt(EXTRACTION_PROMPT))
    assert [e["source"] for e in load_graph(grafo)["edges"]] == ["diego"]


def _diego_largo() -> dict:
    texto = "Diego Fernandez Lopez Monier autoriza las compras grandes."
    return {
        **_triple(texto),
        "subject": "Diego Fernandez Lopez Monier",
        "object": "compras grandes",
    }


def test_la_misma_persona_queda_con_el_nombre_mas_completo_y_su_puesto(grafo: Path) -> None:
    modelo = _PorEsquema(
        {
            "extraccion": {"triples": [_diego_largo()]},
            "misma_persona": {
                "candidates": [{"name": "Diego Fernández", "semantic": 0.9, "confidence": 0.85}]
            },
        }
    )

    result = make_extract_knowledge(Models.same(modelo))(
        {"input": "Diego Fernandez Lopez Monier autoriza las compras grandes."}
    )

    # Es el Jefe de Compras del organigrama: sigue con su puesto, con el nombre largo
    assert (
        "- **Diego Fernandez Lopez Monier** (Jefe de Compras, Farmalog Sur) (era «Diego "
        "Fernández»: ahora **Diego Fernandez Lopez Monier** · score 0,95 · confianza 0,85)"
    ) in result["output"]
    graph = load_graph(grafo)
    assert [(n["id"], n["name"]) for n in graph["nodes"] if n["type"] == "person"] == [
        ("diego-fernandez", "Diego Fernandez Lopez Monier")
    ]
    assert [e for e in graph["edges"] if e["relation"] == "may_be_same"] == []


def test_si_hay_duda_vincula_a_las_dos_personas_para_validar(grafo: Path) -> None:
    modelo = _PorEsquema(
        {
            "extraccion": {"triples": [_diego_largo()]},
            "misma_persona": {
                "candidates": [{"name": "Diego Fernández", "semantic": 0.6, "confidence": 0.3}]
            },
        }
    )

    result = make_extract_knowledge(Models.same(modelo))(
        {"input": "Diego Fernandez Lopez Monier autoriza las compras grandes."}
    )

    assert (
        "(¿será **Diego Fernández**, del organigrama? score 0,80 · confianza 0,30 · "
        "queda para validar)"
    ) in result["output"]
    assert result["output"].endswith("En el grafo: 1 nueva, 1 posible misma persona para validar.")
    # Dos nodos, el nuevo con su relación, y entre ellos la duda con su peso
    graph = load_graph(grafo)
    (doubt,) = [e for e in graph["edges"] if e["relation"] == "may_be_same"]
    assert (doubt["source"], doubt["target"]) == ("diego-fernandez-lopez-monier", "diego-fernandez")
    assert (doubt["status"], doubt["weight"], doubt["confidence"]) == (0, 0.8, 0.3)
    assert doubt["evidence"] == "Diego Fernandez Lopez Monier autoriza las compras grandes."


def test_otra_persona_con_el_mismo_nombre_no_pisa_a_la_que_existe(grafo: Path) -> None:
    texto = "Diego Fernandez del banco Macro nos llamó por un cheque rechazado."
    banquero = {
        **_triple(texto),
        "subject": "Diego Fernandez",
        "object": "cheques rechazados",
        "subject_organization": "Banco Macro",
    }
    modelo = _PorEsquema(
        {
            "extraccion": {"triples": [banquero]},
            "misma_persona": {
                "candidates": [{"name": "Diego Fernández", "semantic": 0.1, "confidence": 0.05}]
            },
        }
    )

    result = make_extract_knowledge(Models.same(modelo))({"input": texto})

    # El nombre limpio, con su empresa al lado (no el puesto del Jefe de Compras)
    assert (
        "- **Diego Fernandez** (Banco Macro) sabe de **cheques rechazados**" in (result["output"])
    )
    graph = load_graph(grafo)
    # Nodo propio, sin paréntesis en el nombre. El modelo lo descartó (0,05): sin duda
    assert [(n["id"], n["name"]) for n in graph["nodes"] if n["type"] == "person"] == [
        ("diego-fernandez-banco-macro", "Diego Fernandez")
    ]
    assert [(e["source"], e["relation"]) for e in graph["edges"]] == [
        ("diego-fernandez-banco-macro", "knows_about")
    ]


def test_al_unificar_queda_el_nombre_mas_completo(grafo: Path) -> None:
    antes = "Diego Hamilton nos avisó de un cheque rechazado."
    save_triples([KnowledgeTriple("Diego Hamilton", "knows_about", "cheques", antes, "high")])
    texto = "Diego Fernandes Hamilton nos explicó la tasa en descubierto."
    hamilton = {**_triple(texto), "subject": "Diego Fernandes Hamilton", "object": "tasas"}
    modelo = _PorEsquema(
        {
            "extraccion": {"triples": [hamilton]},
            "misma_persona": {
                "candidates": [{"name": "Diego Hamilton", "semantic": 0.9, "confidence": 0.9}]
            },
        }
    )

    result = make_extract_knowledge(Models.same(modelo))({"input": texto})

    assert (
        "- **Diego Fernandes Hamilton** (era «Diego Hamilton»: ahora **Diego Fernandes "
        "Hamilton** · score 0,95 · confianza 0,90) sabe de **tasas**"
    ) in result["output"]
    graph = load_graph(grafo)
    # Cambia el nombre, no el id: las dos relaciones siguen en el mismo nodo
    assert [(n["id"], n["name"]) for n in graph["nodes"] if n["type"] == "person"] == [
        ("diego-hamilton", "Diego Fernandes Hamilton")
    ]
    assert [e["source"] for e in graph["edges"]] == ["diego-hamilton", "diego-hamilton"]


def test_sin_relaciones_lo_dice_sin_preguntar(structured_llm) -> None:
    modelo = structured_llm({"triples": []}, reply="¿Me das un ejemplo?")

    result = make_extract_knowledge(Models.same(modelo))({"input": TEXTO})

    assert result == {"output": "No encontré relaciones con respaldo en el texto.", "citations": []}
    assert modelo.seen_reply == []


def test_la_lista_muestra_la_organizacion_de_quien_la_tiene(structured_llm) -> None:
    texto = "Julio Cesar es quien se encarga de manejar nuestra cuenta en el Banco Macro."
    julio = {
        **_triple(texto),
        "subject": "Julio Cesar",
        "object": "cuenta en el Banco Macro",
        "subject_organization": "Banco Macro",
    }

    result = make_extract_knowledge(Models.same(structured_llm({"triples": [julio]})))(
        {"input": texto}
    )

    linea = "- **Julio Cesar** (Banco Macro) sabe de **cuenta en el Banco Macro**"
    assert linea in result["output"]


def test_una_pregunta_se_responde_con_el_grafo(structured_llm, grafo: Path) -> None:
    frase = "Sergio liquida los impuestos el día 10."
    save_triples([KnowledgeTriple("Sergio", "knows_about", "impuestos", frase, "low")], grafo)
    modelo = structured_llm(None)

    result = make_extract_knowledge(Models.same(modelo))({"input": "¿Quién sabe de impuestos?"})

    assert result["output"] == (
        f"De impuestos saben: **Sergio**.\n\nLo que se sabe:\n- «{frase}» (Sergio · confirmada)"
    )
    assert result["citations"] == [frase]
    assert result["referred_to"] == "Sergio"
    # El modelo solo juzga si encaja quien encontraron las palabras (salida rota: queda)
    assert "<personas>" in modelo.seen[0].content


def test_como_se_hace_algo_trae_el_procedimiento_no_escrito(structured_llm, grafo: Path) -> None:
    frase = "Provenzal recupera el backup desde la consola del datacenter."
    save_triples(
        [KnowledgeTriple("Provenzal", "owns_process", "recuperación del backup", frase, "high")],
        grafo,
    )

    result = make_extract_knowledge(Models.same(structured_llm(None)))(
        {"input": "¿Cómo se recupera el backup?"}
    )

    assert f"- «{frase}» (Provenzal · pendiente)" in result["output"]


def test_una_pregunta_sin_nadie_en_el_grafo_lo_dice(structured_llm) -> None:
    node = make_extract_knowledge(Models.same(structured_llm(None)))

    result = node({"input": "quienes se encargan del backup?"})

    assert result["output"] == "No encontré a nadie en el grafo que sepa de backup."


def _joaquin(grafo: Path) -> str:
    frase = "El que más sabe de impuestos es Joaquín Fernández."
    save_triples(
        [KnowledgeTriple("Joaquín Fernández", "knows_about", "impuestos", frase, "low")], grafo
    )
    return frase


def test_sin_coincidencia_el_modelo_elige_el_tema_cercano(structured_llm, grafo: Path) -> None:
    frase = _joaquin(grafo)
    modelo = structured_llm({"topics": ["impuestos"]})

    result = make_extract_knowledge(Models.same(modelo))(
        {"input": "¿Quién es el que más sabe de IVA?"}
    )

    assert result["output"].startswith(
        "No encontré «IVA» en el grafo. Lo más cercano: **impuestos**."
    )
    assert "De impuestos saben: **Joaquín Fernández**." in result["output"]
    assert result["citations"] == [frase]


def test_si_el_modelo_no_ve_nada_cercano_lo_dice(structured_llm, grafo: Path) -> None:
    _joaquin(grafo)
    node = make_extract_knowledge(Models.same(structured_llm({"topics": []})))

    result = node({"input": "¿Quién sabe de cámaras frías?"})

    assert result["output"] == "No encontré a nadie en el grafo que sepa de cámaras frías."


def test_la_respuesta_muestra_el_puesto_de_quien_sabe(structured_llm, grafo: Path) -> None:
    frase = "De desvíos, el que sabe es Ignacio Pereyra."
    save_triples(
        [KnowledgeTriple("Ignacio Pereyra", "knows_about", "desvíos", frase, "low")], grafo
    )
    node = make_extract_knowledge(Models.same(structured_llm(None)))

    result = node({"input": "¿Quién sabe de desvíos?"})

    assert result["output"].startswith(
        "De desvíos saben: **Ignacio Pereyra** "
        "(Gerente de Aseguramiento de Calidad (QA), Farmalog Sur)."
    )


def test_la_organizacion_solo_queda_si_la_nombra_la_frase(structured_llm) -> None:
    texto = "Julio Cesar es quien se encarga de manejar nuestra cuenta en el Banco Macro."
    dicha = {**_triple(texto), "subject": "Julio Cesar", "subject_organization": "Banco Macro"}
    inventada = {**dicha, "subject_organization": "Banco Galicia"}

    assert extract_triples(texto, structured_llm({"triples": [dicha]}))[0].subject_organization == (
        "Banco Macro"
    )
    assert (
        extract_triples(texto, structured_llm({"triples": [inventada]}))[0].subject_organization
        == ""
    )


def test_el_objeto_respeta_como_lo_dice_la_frase(structured_llm) -> None:
    texto = "La persona encargada de descuento de cheques en el banco micro es Ariel Boldrini."
    corregido = {
        **_triple(texto),
        "subject": "Ariel Boldrini",
        "object": "descuento de cheques en el banco macro",
    }
    resumido = {**corregido, "object": "descuento de cheques"}

    (triple,) = extract_triples(texto, structured_llm({"triples": [corregido]}))
    assert triple.object == "descuento de cheques en el banco micro"
    # Lo que el modelo resumió con otras palabras queda como vino
    (triple,) = extract_triples(texto, structured_llm({"triples": [resumido]}))
    assert triple.object == "descuento de cheques"


def test_sin_organizacion_conocida_pide_revision(grafo: Path) -> None:
    def baja(subject: str, evidence: str, organization: str = "") -> KnowledgeTriple:
        return KnowledgeTriple(
            subject, "knows_about", "cheques", evidence, "low", subject_organization=organization
        )

    sin_empresa = baja("Ariel Boldrini", "Ariel Boldrini sabe de cheques.")
    con_empresa = baja("Julio Cesar", "Julio Cesar, del Banco Micro.", "Banco Micro")
    del_organigrama = baja("Ignacio Pereyra", "Ignacio Pereyra sabe de cheques.")
    save_triples([baja("Marta Gil", "Marta Gil, de Droguería Norte.", "Droguería Norte")], grafo)
    de_antes = baja("Marta Gil", "Marta Gil sabe de cheques.")

    revisados = _review_if_unplaced([sin_empresa, con_empresa, del_organigrama, de_antes])

    assert [t.needs_review for t in revisados] == [True, False, False, False]
    assert {t.criticality for t in revisados} == {"low"}  # la criticidad no cambia


def test_sin_organizacion_conocida_queda_pendiente(structured_llm, grafo: Path) -> None:
    texto = "Ariel Boldrini sabe de cheques."
    ariel = {**_triple(texto), "subject": "Ariel Boldrini", "criticality": "low"}

    result = make_extract_knowledge(Models.same(structured_llm({"triples": [ariel]})))(
        {"input": texto}
    )

    assert "criticidad baja · pendiente" in result["output"]


_COBRANZA = (
    "En el día de hoy me presentaron a Ignacio Pereyra quien se encarga de llamar a los "
    "clientes para gestionar los pagos"
)


def _ignacio(criticality: str = "low") -> dict:
    return {
        **_triple(_COBRANZA),
        "subject": "Ignacio Pereyra",
        "relation": "owns_process",
        "object": "llamar a los clientes para gestionar los pagos",
        "criticality": criticality,
    }


def _es_ignacio() -> dict:
    # Es el Ignacio Pereyra del organigrama (Gerente de Calidad)
    return {"candidates": [{"name": "Ignacio Pereyra", "semantic": 0.3, "confidence": 0.9}]}


def test_una_tarea_que_no_encaja_con_el_puesto_queda_pendiente_con_nota(grafo: Path) -> None:
    modelo = _PorEsquema(
        {
            "extraccion": {"triples": [_ignacio()]},
            "misma_persona": _es_ignacio(),
            "encaje_puesto": {
                "checks": [
                    {"index": 0, "fits": False, "reason": "la cobranza la gestiona Tesorería"}
                ]
            },
        }
    )

    result = make_extract_knowledge(Models.same(modelo))({"input": _COBRANZA})

    # Baja y del organigrama: sin el chequeo se confirmaría sola
    assert (
        "criticidad baja · pendiente · ⚠ no coincide con su puesto (Gerente de "
        "Aseguramiento de Calidad (QA)): la cobranza la gestiona Tesorería"
    ) in result["output"]
    (edge,) = load_graph(grafo)["edges"]
    assert edge["status"] == 0
    assert edge["review_note"].startswith("no coincide con su puesto")
    # El modelo ve el puesto oficial y los procedimientos
    pedido = modelo.seen["encaje_puesto"]
    assert "<procedimientos>" in pedido[0].content
    assert "0. Ignacio Pereyra · puesto oficial: Gerente de Aseguramiento" in pedido[1].content


def test_si_encaja_o_el_modelo_no_responde_no_cambia_nada(grafo: Path) -> None:
    for chequeo in ({"checks": [{"index": 0, "fits": True, "reason": ""}]}, None):
        grafo.unlink(missing_ok=True)
        modelo = _PorEsquema(
            {
                "extraccion": {"triples": [_ignacio()]},
                "misma_persona": _es_ignacio(),
                "encaje_puesto": chequeo,
            }
        )

        result = make_extract_knowledge(Models.same(modelo))({"input": _COBRANZA})

        assert "criticidad baja · confirmada" in result["output"]
        assert "⚠" not in result["output"]


def test_gente_de_afuera_no_se_chequea_contra_el_puesto(grafo: Path) -> None:
    texto = "Julio Cesar, del Banco Macro, sabe de cheques."
    julio = {**_triple(texto), "subject": "Julio Cesar", "object": "cheques"}
    julio["subject_organization"] = "Banco Macro"
    modelo = _PorEsquema({"extraccion": {"triples": [julio]}})

    make_extract_knowledge(Models.same(modelo))({"input": texto})

    assert "encaje_puesto" not in modelo.seen


def test_en_trabaja_con_el_objeto_tambien_se_resuelve_como_persona(grafo: Path) -> None:
    texto = "Ana Ruiz trabaja codo a codo con Pablo Sossa."
    modelo = _PorEsquema(
        {
            "extraccion": {
                "triples": [
                    {
                        **_triple(texto),
                        "subject": "Ana Ruiz",
                        "relation": "works_with",
                        "object": "Pablo Sossa",
                    }
                ]
            },
            "misma_persona": {
                "candidates": [
                    {"name": "Ana Ruiz", "semantic": 0.95, "confidence": 0.9},
                    {"name": "Pablo Sosa", "semantic": 0.95, "confidence": 0.9},
                ]
            },
        }
    )

    result = make_extract_knowledge(Models.same(modelo))({"input": texto})

    # "Pablo Sossa" es Pablo Sosa del organigrama: la relación va a su nodo
    assert "trabaja con **Pablo Sosa**" in result["output"]
    edges = [e for e in load_graph(grafo)["edges"] if e["relation"] == "works_with"]
    assert [(e["source"], e["target"]) for e in edges] == [("ana-ruiz", "pablo-sosa")]


TABLA = "Diego hizo la tabla dinámica del informe de ventas. El informe de ventas es un Excel."
HIZO = "Diego hizo la tabla dinámica del informe de ventas."


def _deducida(tool: str, source: str = "conversación", evidence: str = HIZO) -> dict:
    return {
        "subject": "Diego",
        "tool": tool,
        "evidence": evidence,
        "source": source,
        "reason": f"hizo la tabla dinámica del informe de ventas, que se hace en {tool}",
    }


def test_el_esquema_pide_lo_deducido_aparte() -> None:
    item = _SCHEMA["properties"]["inferred"]["items"]

    assert "inferred" in _SCHEMA["required"]
    assert set(item["required"]) == {"subject", "tool", "evidence", "source", "reason"}


def test_la_herramienta_deducida_va_baja_pendiente_y_con_su_motivo(structured_llm) -> None:
    modelo = structured_llm({"triples": [], "inferred": [_deducida("Excel")]})

    (triple,) = extract_triples(TABLA, modelo)

    assert (triple.subject, triple.relation, triple.object) == ("Diego", "knows_about", "Excel")
    assert (triple.evidence, triple.criticality) == (HIZO, "low")
    assert triple.inferred and triple.needs_review
    assert triple.review_note == (
        "deducido: hizo la tabla dinámica del informe de ventas, que se hace en Excel "
        "(lo dice la conversación)"
    )


def test_una_herramienta_que_nadie_nombra_no_se_deduce(structured_llm) -> None:
    # Ni la conversación ni el documento citado dicen Google Sheets: la inventó
    texto = HIZO
    inventadas = [_deducida("Google Sheets"), _deducida("Google Sheets", "compras.md")]
    modelo = structured_llm({"triples": [], "inferred": inventadas})

    assert extract_triples(texto, modelo) == []


def test_la_frase_de_lo_deducido_tiene_que_estar_textual(structured_llm) -> None:
    parafraseada = _deducida("Excel", evidence="Diego armó la tabla dinámica.")
    modelo = structured_llm({"triples": [], "inferred": [parafraseada]})

    assert extract_triples(TABLA, modelo) == []


def test_la_herramienta_puede_salir_de_un_procedimiento(structured_llm) -> None:
    texto = "Rocío Sanz sabe hacer el ajuste de inventario cuando el conteo no cierra."
    ajuste = {
        "subject": "Rocío Sanz",
        "tool": "Sigma WMS",
        "evidence": texto,
        "source": "sigma-wms.md",
        "reason": "hace ajustes de inventario, que se hacen en Sigma WMS",
    }
    modelo = structured_llm({"triples": [], "inferred": [ajuste]})

    (triple,) = extract_triples(texto, modelo)

    assert triple.object == "Sigma WMS" and triple.inferred
    assert triple.review_note.endswith("(lo dice sigma-wms.md)")


def test_si_ya_se_dijo_no_se_repite_como_deducida(structured_llm) -> None:
    texto = "Diego sabe de Excel. Diego hizo la tabla dinámica del informe de ventas."
    dicha = {**_triple("Diego sabe de Excel."), "object": "Excel"}
    modelo = structured_llm({"triples": [dicha], "inferred": [_deducida("Excel")]})

    (triple,) = extract_triples(texto, modelo)

    assert not triple.inferred and triple.evidence == "Diego sabe de Excel."


def test_el_nodo_guarda_la_deducida_pendiente_y_la_marca(grafo: Path) -> None:
    modelo = _PorEsquema({"extraccion": {"triples": [], "inferred": [_deducida("Excel")]}})

    result = make_extract_knowledge(Models.same(modelo))({"input": TABLA})

    assert "sabe de **Excel** (deducida)" in result["output"]
    assert "⚠ deducido: hizo la tabla dinámica" in result["output"]
    (edge,) = load_graph(grafo)["edges"]
    assert edge["inferred"] is True and edge["status"] == 0  # pendiente
    # Ya pide revisión: no se le pregunta al modelo si encaja con el puesto
    assert "encaje_puesto" not in modelo.seen


SUPERSET = "El tablero de Gestión es de Superset."


def _herramienta(thing: str = "tablero de Gestión", tool: str = "Superset") -> dict:
    return {"thing": thing, "tool": tool, "evidence": SUPERSET}


def test_el_esquema_pide_con_que_herramienta_se_hace_algo() -> None:
    assert "tool_facts" in _SCHEMA["required"]
    item = _SCHEMA["properties"]["tool_facts"]["items"]
    assert set(item["required"]) == {"thing", "tool", "evidence"}


def test_una_herramienta_sin_persona_se_cruza_con_el_grafo(grafo: Path) -> None:
    santiago = KnowledgeTriple(
        "Santiago Sosa Suarez",
        "owns_process",
        "tablero de Gestión",
        "Santiago Sosa Suarez se encarga del tablero de Gestión.",
        "medium",
    )
    save_triples([santiago], grafo)
    modelo = _PorEsquema(
        {"extraccion": {"triples": [], "inferred": [], "tool_facts": [_herramienta()]}}
    )

    result = make_extract_knowledge(Models.same(modelo))({"input": SUPERSET})

    assert "**Santiago Sosa Suarez** sabe de **Superset** (deducida)" in result["output"]
    assert (
        "Anoté en el grafo:\n- **tablero de Gestión** se hace con **Superset**" in result["output"]
    )
    deducida = next(e for e in load_graph(grafo)["edges"] if e.get("inferred"))
    assert (deducida["source"], deducida["target"]) == ("santiago-sosa-suarez", "superset")


def test_una_herramienta_que_la_frase_no_nombra_se_descarta(grafo: Path) -> None:
    inventada = _herramienta(tool="Power BI")
    modelo = _PorEsquema({"extraccion": {"triples": [], "inferred": [], "tool_facts": [inventada]}})

    result = make_extract_knowledge(Models.same(modelo))({"input": SUPERSET})

    assert result["output"] == "No encontré relaciones con respaldo en el texto."
    assert load_graph(grafo) == {"nodes": [], "edges": []}

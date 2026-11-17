"""La resolución de personas, con un modelo de salida fija: sin red y determinístico.

Se prueba el cálculo alrededor del modelo (candidatos, score, decisión y cuándo no se
lo llama), no qué tan bien juzga el modelo.
"""

from pathlib import Path

import pytest
from pydantic import BaseModel

from onboarding.agents.extract_knowledge.identity import (
    OUTPUT_TOKENS,
    PersonMatch,
    invoke_structured,
    resolve_person,
    with_output_room,
)
from onboarding.knowledge import KnowledgeTriple, save_triples


@pytest.fixture(autouse=True)
def grafo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Solo el organigrama: el grafo empieza vacío, en un archivo temporal
    path = tmp_path / "grafo.json"
    monkeypatch.setattr("onboarding.knowledge.informal_network.store.GRAPH_PATH", path)
    return path


FRASE = "Diego Fernandez Lopez Monier autoriza las compras grandes."


def _juicio(name: str, semantic: float, confidence: float) -> dict:
    return {"candidates": [{"name": name, "semantic": semantic, "confidence": confidence}]}


def test_el_mismo_nombre_tambien_lo_juzga_el_modelo(structured_llm) -> None:
    modelo = structured_llm(_juicio("Julián Rearte", 0.9, 0.9))

    match = resolve_person("julian rearte", "Julián Rearte sabe de desvíos.", model=modelo)

    assert match == PersonMatch(
        "julian rearte",
        "Julián Rearte",
        "organigrama",
        1.0,
        0.9,
        0.95,
        0.9,
        "same",
        "julian-rearte",
    )
    assert "Frase: Julián Rearte sabe de desvíos." in modelo.seen[1].content


def test_un_homonimo_de_otra_empresa_se_guarda_aparte(structured_llm) -> None:
    # La extracción no completó la empresa: el modelo la lee en la frase
    frase = "Diego Fernandez nos llamó del banco Macro por un cheque rechazado."
    modelo = structured_llm(_juicio("Diego Fernández", 0.1, 0.1))

    match = resolve_person("Diego Fernandez", frase, model=modelo)

    # score 0,55, pero el modelo casi lo descarta (0,1): otra persona, sin duda. Se
    # guarda en un nodo propio, con el nombre limpio
    assert (match.decision, match.score, match.confidence) == ("new", 0.55, 0.1)
    assert (match.name, match.save_id) == ("Diego Fernandez", "Diego Fernandez homonimo")
    with_company = resolve_person(
        "Diego Fernandez", frase, organization="Banco Macro", model=modelo
    )
    assert with_company.save_id == "Diego Fernandez Banco Macro"


def test_el_mismo_nombre_y_un_solo_candidato_es_la_misma_persona(structured_llm) -> None:
    # Lo que juzgó el modelo con "Diego Fernández se encarga de mantener los controles
    # de acceso al depósito de librería": score 0,75 y confianza 0,6, antes en duda
    frase = "Diego Fernández se encarga de mantener los controles de acceso al depósito."
    for confidence, decision in ((0.6, "same"), (0.5, "same"), (0.49, "maybe")):
        match = resolve_person(
            "Diego Fernández",
            frase,
            model=structured_llm(_juicio("Diego Fernández", 0.5, confidence)),
        )

        assert (match.score, match.decision) == (0.75, decision)
    # Si la frase dice otra organización, no alcanza con el nombre
    match = resolve_person(
        "Diego Fernández",
        frase,
        organization="Banco Micro",
        model=structured_llm(_juicio("Diego Fernández", 0.5, 0.6)),
    )
    assert match.decision == "maybe"


def test_con_confianza_minima_queda_en_duda(structured_llm) -> None:
    for confidence, decision in ((0.3, "maybe"), (0.29, "new")):
        match = resolve_person(
            "Diego Fernandez Lopez Monier",
            FRASE,
            model=structured_llm(_juicio("Diego Fernández", 0.2, confidence)),
        )

        # score 0,6: alcanza para la duda solo si el modelo no lo descarta
        assert (match.score, match.decision) == (0.6, decision)


def test_sin_nombres_parecidos_es_nueva_sin_llamar_al_modelo(structured_llm) -> None:
    modelo = structured_llm(None)

    match = resolve_person("Julio Cesar", "Julio Cesar maneja la cuenta.", model=modelo)

    assert (match.decision, match.candidate) == ("new", None)
    assert modelo.seen == []


def test_score_y_confianza_altos_es_la_misma_persona(structured_llm) -> None:
    modelo = structured_llm(_juicio("Diego Fernández", 0.9, 0.85))

    match = resolve_person("Diego Fernandez Lopez Monier", FRASE, model=modelo)

    # score = 0,5 × literal (1) + 0,5 × semántica (0,9)
    assert match == PersonMatch(
        "Diego Fernandez Lopez Monier",
        "Diego Fernández",
        "organigrama",
        1.0,
        0.9,
        0.95,
        0.85,
        "same",
        "diego-fernandez",
    )


def test_sin_confianza_del_modelo_queda_en_duda(structured_llm) -> None:
    match = resolve_person(
        "Diego Fernandez Lopez Monier",
        FRASE,
        model=structured_llm(_juicio("Diego Fernández", 0.9, 0.4)),
    )

    assert (match.decision, match.score, match.confidence) == ("maybe", 0.95, 0.4)


def test_sin_semantica_suficiente_queda_en_duda_aunque_el_nombre_coincida(
    structured_llm,
) -> None:
    match = resolve_person(
        "Diego Fernandez Lopez Monier",
        FRASE,
        model=structured_llm(_juicio("Diego Fernández", 0.5, 0.75)),
    )

    # score 0,75 y confianza 0,75 alcanzan, pero la semántica (0,5) no llega a 0,6
    assert (match.decision, match.score, match.semantic) == ("maybe", 0.75, 0.5)


def test_con_el_modelo_muy_seguro_no_hace_falta_la_semantica(structured_llm) -> None:
    # La frase no habla del puesto: semántica 0,5. Pero el modelo está seguro (0,85)
    match = resolve_person(
        "Julián Rearte",
        "A Julián Rearte me lo presentó Ignacio Pereyra.",
        model=structured_llm(_juicio("Julián Rearte", 0.5, 0.85)),
    )

    assert (match.decision, match.score, match.candidate_id) == ("same", 0.75, "julian-rearte")


def _dos_diegos() -> None:
    # Un Diego Fernández en el organigrama y otro, del banco, en el grafo
    frase = "Diego Fernandez del Banco Macro maneja la cuenta."
    banquero = KnowledgeTriple(
        "Diego Fernandez",
        "owns_process",
        "cuenta",
        frase,
        "low",
        subject_id="Diego Fernandez Banco Macro",
    )
    save_triples([banquero])


def _juicios(*items: tuple[str, float, float]) -> dict:
    return {"candidates": [{"name": n, "semantic": s, "confidence": c} for n, s, c in items]}


def test_dos_candidatos_creibles_y_empatados_quedan_en_duda(structured_llm) -> None:
    _dos_diegos()
    modelo = structured_llm(_juicios(("Diego Fernández", 0.9, 0.9), ("Diego Fernandez", 0.85, 0.8)))

    match = resolve_person("Diego Fernandez", "Diego Fernandez sabe de pagos.", model=modelo)

    # 0,95 contra 0,93: el modelo no tiene cómo elegir entre los dos
    assert (match.decision, match.candidate, match.score) == ("maybe", "Diego Fernández", 0.95)


def test_si_el_otro_candidato_no_es_creible_no_hay_empate(structured_llm) -> None:
    _dos_diegos()
    modelo = structured_llm(_juicios(("Diego Fernández", 0.9, 0.9), ("Diego Fernandez", 0.85, 0.1)))

    match = resolve_person("Diego Fernandez", "Diego Fernandez sabe de pagos.", model=modelo)

    assert (match.decision, match.candidate_id) == ("same", "diego-fernandez")


def test_score_bajo_es_una_persona_nueva(structured_llm) -> None:
    match = resolve_person(
        "Diego",
        "Diego, el del Banco Macro, maneja nuestra cuenta.",
        organization="Banco Macro",
        model=structured_llm(_juicio("Diego Fernández", 0.1, 0.9)),
    )

    # literal 0,6 (un solo nombre) y semántica 0,1: score 0,35
    assert (match.decision, match.score) == ("new", 0.35)


def test_un_candidato_inventado_o_una_salida_rota_no_suman(structured_llm) -> None:
    for salida in (_juicio("Diego Inventado", 1.0, 1.0), None, {"candidates": "roto"}):
        match = resolve_person("Diego Fernandez Lopez Monier", FRASE, model=structured_llm(salida))

        # Solo cuenta el parecido literal: 0,5 × 1 = 0,5, pero sin confianza no hay duda
        assert (match.semantic, match.confidence, match.decision) == (0.0, 0.0, "new")


def test_el_modelo_ve_la_frase_y_el_puesto_del_candidato(structured_llm) -> None:
    modelo = structured_llm(_juicio("Diego Fernández", 0.9, 0.9))

    resolve_person("Diego Fernandez Lopez Monier", FRASE, position="comprador", model=modelo)

    mention = modelo.seen[1].content
    assert f"Frase: {FRASE}" in mention
    assert "Puesto: comprador" in mention
    assert "- Diego Fernández · Jefe de Compras · Farmalog Sur (organigrama)" in mention


class _Modelo(BaseModel):
    max_tokens: int | None = None


def test_con_tope_chico_le_da_lugar_para_razonar() -> None:
    modelo = _Modelo(max_tokens=1024)

    assert with_output_room(modelo).max_tokens == OUTPUT_TOKENS
    assert modelo.max_tokens == 1024  # el de los demás no cambia


def test_con_tope_grande_o_sin_tope_queda_como_esta() -> None:
    assert with_output_room(_Modelo(max_tokens=16000)).max_tokens == 16000
    assert with_output_room(_Modelo()).max_tokens is None


class LengthFinishReasonError(Exception):
    """Con el mismo nombre que el de OpenAI: el reintento lo reconoce por el nombre."""


class _ModeloQueSeCorta(BaseModel):
    """Falla por largo con tope chico; con lugar, responde. Anota cada tope que usó."""

    max_tokens: int = 1024
    error: type[Exception] = LengthFinishReasonError
    topes: list[int] = []

    def with_structured_output(self, schema: dict, method: str) -> "_ModeloQueSeCorta":
        return self

    def invoke(self, messages: list) -> dict:
        self.topes.append(self.max_tokens)
        if self.max_tokens < OUTPUT_TOKENS:
            raise self.error("no entró")
        return {"ok": True}


def test_si_no_entra_reintenta_una_vez_con_mas_lugar() -> None:
    modelo = _ModeloQueSeCorta()

    assert invoke_structured(modelo, {}, []) == {"ok": True}
    assert modelo.topes == [1024, OUTPUT_TOKENS]


def test_si_entra_no_reintenta() -> None:
    modelo = _ModeloQueSeCorta(max_tokens=OUTPUT_TOKENS)

    assert invoke_structured(modelo, {}, []) == {"ok": True}
    assert modelo.topes == [OUTPUT_TOKENS]


def test_otro_error_no_se_reintenta() -> None:
    modelo = _ModeloQueSeCorta(error=ValueError)

    with pytest.raises(ValueError):
        invoke_structured(modelo, {}, [])
    assert modelo.topes == [1024]

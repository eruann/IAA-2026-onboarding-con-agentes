"""La extracción se prueba con un modelo de salida fija: sin red y determinístico.

Lo que se testea acá es lo que hace el código alrededor del modelo (el filtro de
evidencia y el contexto que recibe), no la calidad de la extracción. Eso se mide
en eval/.
"""

from langchain_core.messages import SystemMessage

from onboarding.knowledge.informal_network.extraction import KnowledgeTriple, extract_triples

TEXTO = "Para Excel avanzado, preguntale a Diego. Es un genio."


class _ModeloFijo:
    """Devuelve siempre la misma salida estructurada y guarda los mensajes que recibió.

    FakeListChatModel no sirve acá: no implementa with_structured_output.
    """

    def __init__(self, salida: dict | None) -> None:
        self.salida = salida
        self.mensajes: list = []

    def with_structured_output(self, schema: dict, method: str) -> "_ModeloFijo":
        return self

    def invoke(self, mensajes: list) -> dict | None:
        self.mensajes = mensajes
        return self.salida


def _triple(evidence: str) -> dict:
    return {
        "subject": "Diego",
        "relation": "knows_about",
        "object": "Excel avanzado",
        "evidence": evidence,
    }


def test_relacion_con_evidencia_textual_se_devuelve() -> None:
    modelo = _ModeloFijo({"triples": [_triple("Para Excel avanzado, preguntale a Diego.")]})

    triples = extract_triples(TEXTO, modelo)

    assert triples == [
        KnowledgeTriple(
            subject="Diego",
            relation="knows_about",
            object="Excel avanzado",
            evidence="Para Excel avanzado, preguntale a Diego.",
        )
    ]


def test_relacion_con_evidencia_inventada_se_descarta() -> None:
    modelo = _ModeloFijo({"triples": [_triple("Diego sabe mucho de Excel.")]})

    assert extract_triples(TEXTO, modelo) == []


def test_salida_vacia_del_modelo_devuelve_lista_vacia() -> None:
    assert extract_triples(TEXTO, _ModeloFijo(None)) == []
    assert extract_triples(TEXTO, _ModeloFijo({"triples": []})) == []


def test_el_prompt_lleva_organigrama_y_procedimientos() -> None:
    modelo = _ModeloFijo(None)

    extract_triples(TEXTO, modelo)

    system = modelo.mensajes[0]
    assert isinstance(system, SystemMessage)
    assert "<organigrama>" in system.content
    assert "<procedimientos>" in system.content
    assert '<documento nombre="compras.md">' in system.content
    assert '<documento nombre="README.md">' not in system.content
    assert '<documento nombre="organigrama.md">' not in system.content

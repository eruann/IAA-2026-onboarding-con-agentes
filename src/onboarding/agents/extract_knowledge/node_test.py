"""El nodo se prueba con un modelo de salida fija: lo que importa es cómo arma la
respuesta con lo que devuelve extract_triples, no la calidad de la extracción."""

from onboarding.agents.extract_knowledge import make_extract_knowledge

TEXTO = "Para Excel avanzado, preguntale a Diego."


class _ModeloFijo:
    def __init__(self, salida: dict | None) -> None:
        self.salida = salida

    def with_structured_output(self, schema: dict, method: str) -> "_ModeloFijo":
        return self

    def invoke(self, mensajes: list) -> dict | None:
        return self.salida


def test_lista_las_relaciones_con_su_respaldo() -> None:
    triple = {
        "subject": "Diego",
        "relation": "knows_about",
        "object": "Excel avanzado",
        "evidence": "Para Excel avanzado, preguntale a Diego.",
    }
    node = make_extract_knowledge(_ModeloFijo({"triples": [triple]}))

    result = node({"input": TEXTO})

    assert "**Diego** sabe de **Excel avanzado**" in result["output"]
    assert result["citations"] == ["Para Excel avanzado, preguntale a Diego."]


def test_sin_relaciones_lo_dice() -> None:
    node = make_extract_knowledge(_ModeloFijo({"triples": []}))

    assert node({"input": TEXTO}) == {
        "output": "No encontré relaciones con respaldo en el texto.",
        "citations": [],
    }

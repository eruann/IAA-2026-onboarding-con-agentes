import pytest
from langchain_core.messages import AIMessage, HumanMessage

from onboarding.agents.answer_question import NODE, make_answer_question
from onboarding.agents.answer_question import node as node_module
from onboarding.knowledge import RetrievedChunk

CHUNK = RetrievedChunk(
    text="Las compras las pide el formulario interno.",
    document="compras.md",
    section="Pedido de compra",
    score=0.8,
)


@pytest.fixture
def fake_retrieve(monkeypatch):
    def _set(chunks: list[RetrievedChunk]):
        monkeypatch.setattr(node_module, "retrieve", lambda query, k=5: chunks)

    return _set


def test_responde_con_los_fragmentos_el_nombre_y_la_conversacion(
    recording_llm, fake_retrieve
) -> None:
    fake_retrieve([CHUNK])
    node = make_answer_question(recording_llm)

    result = node(
        {
            "input": "¿Cómo pido una compra?",
            "actor_name": "Ana",
            "messages": [HumanMessage("Hola"), AIMessage("Hola, ¿en qué te ayudo?")],
        }
    )

    system, *rest = recording_llm.seen[0]
    assert system.content.startswith(NODE.prompt.read_text(encoding="utf-8"))
    assert '<fragmento documento="compras.md" seccion="Pedido de compra">' in system.content
    assert "Las compras las pide el formulario interno." in system.content
    assert "La persona se llama Ana" in system.content
    assert [m.content for m in rest] == [
        "Hola",
        "Hola, ¿en qué te ayudo?",
        "¿Cómo pido una compra?",
    ]
    assert result == {
        "output": "respuesta de prueba",
        "citations": ["compras.md § Pedido de compra"],
        "referred_to": None,
    }


def test_sin_fragmentos_deriva_con_quien_sabe_del_tema(
    recording_llm, fake_retrieve, monkeypatch
) -> None:
    fake_retrieve([])
    monkeypatch.setattr(node_module, "who_knows_about", lambda topic: ["Romina Castro"])
    node = make_answer_question(recording_llm)

    result = node({"input": "¿Puedo traer a mi mascota?"})

    assert result["citations"] == []
    assert result["referred_to"] == "Romina Castro"
    assert "no se encontró documentación relacionada" in recording_llm.seen[0][0].content


def test_sin_fragmentos_y_sin_grafo_todavia_no_deriva_a_nadie(
    recording_llm, fake_retrieve, monkeypatch
) -> None:
    fake_retrieve([])

    def _not_implemented(topic: str) -> list[str]:
        raise NotImplementedError("TODO(grafo): consulta del grafo")

    monkeypatch.setattr(node_module, "who_knows_about", _not_implemented)
    node = make_answer_question(recording_llm)

    result = node({"input": "¿Puedo traer a mi mascota?"})

    assert result["referred_to"] is None

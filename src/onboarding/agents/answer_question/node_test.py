from langchain_core.messages import AIMessage, HumanMessage

from onboarding.agents.answer_question import NODE, make_answer_question
from onboarding.agents.common import Models


def test_responde_con_los_documentos_el_nombre_y_la_conversacion(recording_llm) -> None:
    node = make_answer_question(Models.same(recording_llm))

    result = node(
        {
            "input": "¿y quién lo reemplaza?",
            "actor_name": "Ana",
            "messages": [HumanMessage("¿Quién es el Jefe de Tesorería?"), AIMessage("Federico")],
        }
    )

    system, *rest = recording_llm.seen[0]
    assert system.content.startswith(NODE.prompt.read_text(encoding="utf-8"))
    assert '<documento nombre="tesoreria.md">' in system.content
    assert "La persona se llama Ana" in system.content
    assert [m.content for m in rest] == [
        "¿Quién es el Jefe de Tesorería?",
        "Federico",
        "¿y quién lo reemplaza?",
    ]
    assert result == {"output": "respuesta de prueba", "citations": [], "referred_to": None}

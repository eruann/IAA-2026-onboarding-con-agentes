from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from onboarding.agents.common import Models, ask_model


def test_un_mismo_modelo_para_todos_los_perfiles(recording_llm) -> None:
    models = Models.same(recording_llm)

    assert models.main is recording_llm
    assert models.structured is recording_llm


def test_ask_model_arma_prompt_contexto_nombre_y_conversacion(
    tmp_path: Path, recording_llm
) -> None:
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Sos un agente de prueba.", encoding="utf-8")
    state = {
        "input": "¿Y ahora?",
        "messages": [HumanMessage("Hola"), AIMessage("Hola, ¿qué necesitás?")],
        "actor_name": "Ana",
    }

    answer = ask_model(recording_llm, prompt, state, context="<datos>x</datos>")

    assert answer == "respuesta de prueba"
    system, *previous, question = recording_llm.seen[0]
    assert isinstance(system, SystemMessage)
    assert system.content.startswith("Sos un agente de prueba.\n\n<datos>x</datos>")
    assert "La persona se llama Ana" in system.content
    assert [m.content for m in previous] == ["Hola", "Hola, ¿qué necesitás?"]
    assert question == HumanMessage("¿Y ahora?")

from langchain_core.language_models import FakeListChatModel

from onboarding.agents import run_turn


def test_un_turno_devuelve_respuesta_agente_y_recorrido(fake_llm: FakeListChatModel) -> None:
    result = run_turn("¿cómo pido una compra?", person_key="ana-ingresante", model=fake_llm)

    assert result.output == "respuesta de prueba"
    assert result.agent == "answer_question"
    assert result.path == ["coordinator", "answer_question", "extract_knowledge"]


def test_el_agente_elegido_atiende_el_turno(fake_llm: FakeListChatModel) -> None:
    result = run_turn("ya hice la misión", agent="quests", model=fake_llm)

    assert result.agent == "quests"
    assert ("quests", {"output": "respuesta de prueba"}) in result.steps


class _ModeloQueAnota(FakeListChatModel):
    """Fake que guarda los mensajes que recibió."""

    seen: list = []

    def invoke(self, messages, *args, **kwargs):
        self.seen.append(messages)
        return super().invoke(messages, *args, **kwargs)


def test_la_conversacion_previa_le_llega_al_modelo() -> None:
    model = _ModeloQueAnota(responses=["ok"])

    run_turn(
        "¿y la segunda?",
        history=[("user", "¿cuál es la primera misión?"), ("assistant", "Almorzar con Logística")],
        model=model,
    )

    contents = [message.content for message in model.seen[0]]
    assert "¿cuál es la primera misión?" in contents
    assert "Almorzar con Logística" in contents
    assert contents[-1] == "¿y la segunda?"

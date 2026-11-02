import pytest
from langchain_core.language_models import FakeListChatModel

from onboarding.agents import TurnError, run_turn


class _ModeloQueAnota(FakeListChatModel):
    """Fake que guarda los mensajes que recibió."""

    seen: list = []

    def invoke(self, messages, *args, **kwargs):
        self.seen.append(messages)
        return super().invoke(messages, *args, **kwargs)


def test_un_turno_devuelve_respuesta_y_recorrido(fake_llm: FakeListChatModel) -> None:
    result = run_turn("¿Quién es el Jefe de Tesorería?", model=fake_llm)

    assert result.output == "respuesta de prueba"
    assert result.path == ["answer_question"]


def test_conocimiento_recibe_los_documentos_el_nombre_y_la_conversacion() -> None:
    model = _ModeloQueAnota(responses=["ok"])

    run_turn(
        "¿y quién lo reemplaza?",
        actor_name="Ana",
        history=[("user", "¿Quién es el Jefe de Tesorería?"), ("assistant", "Federico Medina")],
        model=model,
    )

    system, *rest = model.seen[0]
    assert '<documento nombre="tesoreria.md">' in system.content
    assert "La persona se llama Ana" in system.content
    assert [m.content for m in rest] == [
        "¿Quién es el Jefe de Tesorería?",
        "Federico Medina",
        "¿y quién lo reemplaza?",
    ]


class _ModeloQueFalla(FakeListChatModel):
    def invoke(self, *args, **kwargs):
        raise RuntimeError("el proveedor no responde")


def test_si_falla_dice_en_que_nodo_y_guarda_el_error_original() -> None:
    with pytest.raises(TurnError) as failure:
        run_turn("¿Quién es el Jefe de Tesorería?", model=_ModeloQueFalla(responses=["x"]))

    assert failure.value.path == []
    assert failure.value.failed_node == "answer_question"
    assert isinstance(failure.value.__cause__, RuntimeError)

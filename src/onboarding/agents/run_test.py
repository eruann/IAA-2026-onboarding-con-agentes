import pytest
from langchain_core.language_models import FakeListChatModel

from onboarding.agents import TurnError, path_text, run_turn


def test_un_turno_devuelve_respuesta_y_recorrido(fake_llm: FakeListChatModel) -> None:
    result = run_turn("¿Quién es el Jefe de Tesorería?", model=fake_llm)

    assert result.output == "respuesta de prueba"
    assert result.path == ["answer_question"]


def test_pasa_el_nombre_y_la_conversacion_al_nodo(recording_llm) -> None:
    run_turn(
        "¿y quién lo reemplaza?",
        actor_name="Ana",
        history=[("user", "¿Quién es el Jefe de Tesorería?"), ("assistant", "Federico Medina")],
        model=recording_llm,
    )

    system, *rest = recording_llm.seen[0]
    assert "La persona se llama Ana" in system.content
    assert [m.content for m in rest] == [
        "¿Quién es el Jefe de Tesorería?",
        "Federico Medina",
        "¿y quién lo reemplaza?",
    ]


def test_si_falla_dice_en_que_nodo_y_guarda_el_error_original(failing_llm) -> None:
    with pytest.raises(TurnError) as failure:
        run_turn("¿Quién es el Jefe de Tesorería?", model=failing_llm)

    assert failure.value.path == []
    assert failure.value.failed_node == "answer_question"
    assert isinstance(failure.value.__cause__, RuntimeError)


def test_el_recorrido_dice_hasta_donde_llego_si_fallo() -> None:
    assert path_text(["answer_question"]) == "Recorrido: Inicio → answer_question → Fin"
    assert path_text([], "answer_question") == "Recorrido: Inicio → answer_question ✗"

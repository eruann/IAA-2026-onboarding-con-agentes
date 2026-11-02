from onboarding.ui.pages import next_model, path_caption


def test_el_modelo_siguiente_vuelve_al_principio_al_final_de_la_lista() -> None:
    assert next_model(0, 3) == 1
    assert next_model(2, 3) == 0
    # Con un solo modelo no hay a cuál pasar
    assert next_model(0, 1) is None


def test_el_recorrido_dice_hasta_donde_llego_si_fallo() -> None:
    assert path_caption(["answer_question"]) == "Recorrido: Inicio → answer_question → Fin"
    assert path_caption([], "answer_question") == "Recorrido: Inicio → answer_question ✗"

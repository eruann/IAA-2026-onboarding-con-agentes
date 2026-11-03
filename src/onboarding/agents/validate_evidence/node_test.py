from onboarding.agents.validate_evidence import NODE, make_validate_evidence


def test_revisa_la_evidencia_con_su_prompt(recording_llm) -> None:
    node = make_validate_evidence(recording_llm)

    result = node({"input": "Adjunto la captura del primer mail."})

    system, evidence = recording_llm.seen[0]
    assert system.content == NODE.prompt.read_text(encoding="utf-8")
    assert evidence.content == "Adjunto la captura del primer mail."
    assert result == {"output": "respuesta de prueba"}

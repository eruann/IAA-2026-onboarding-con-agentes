from langchain_core.language_models import FakeListChatModel

from onboarding.agents.generate_quest import make_generate_quest


class _ModeloQueAnota(FakeListChatModel):
    """Fake que guarda los mensajes que recibió."""

    seen: list = []

    def invoke(self, messages, *args, **kwargs):
        self.seen.append(messages)
        return super().invoke(messages, *args, **kwargs)


def test_propone_con_su_prompt_y_el_pedido() -> None:
    model = _ModeloQueAnota(responses=["- key: nueva"])
    node = make_generate_quest(model)

    result = node({"input": "Misiones para un analista de Tesorería"})

    system, pedido = model.seen[0]
    assert "Diseñás misiones de onboarding" in system.content
    assert pedido.content == "Misiones para un analista de Tesorería"
    assert result == {"output": "- key: nueva"}

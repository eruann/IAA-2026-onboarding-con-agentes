import pytest

from onboarding.agents.tools import pending_missions, search_documentation, who_knows


@pytest.mark.parametrize("tool", [search_documentation, who_knows, pending_missions])
def test_las_tools_todavia_son_pendientes(tool) -> None:
    # Cuando se implemente una, este test se cambia por uno de lo que hace
    with pytest.raises(NotImplementedError, match=r"TODO\(agentes\)"):
        tool("x")

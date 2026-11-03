import pytest

from onboarding.agents.tools import pending_missions, search_documentation, who_knows
from onboarding.workshop import is_pending


@pytest.mark.parametrize("tool", [search_documentation, who_knows, pending_missions])
def test_las_tools_todavia_son_pendientes(tool) -> None:
    # Cuando se implemente una, este test se cambia por uno de lo que hace
    assert is_pending(tool)

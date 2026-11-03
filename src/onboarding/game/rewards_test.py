import pytest

from onboarding.game.rewards import list_rewards, redeem, redemption_history
from onboarding.workshop import is_pending


@pytest.mark.parametrize("function", [list_rewards, redeem, redemption_history])
def test_el_canje_todavia_es_pendiente(function) -> None:
    # Cuando se implemente una, este test se cambia por uno de lo que hace
    assert is_pending(function)

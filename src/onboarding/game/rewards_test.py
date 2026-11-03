import pytest

from onboarding.game.rewards import list_rewards, redeem, redemption_history


@pytest.mark.parametrize(
    ("function", "args"),
    [(list_rewards, ()), (redeem, ("ana", "cafe")), (redemption_history, ("ana",))],
)
def test_el_canje_todavia_es_pendiente(function, args) -> None:
    # Cuando se implemente una, este test se cambia por uno de lo que hace
    with pytest.raises(NotImplementedError, match=r"TODO\(experiencia\)"):
        function(*args)

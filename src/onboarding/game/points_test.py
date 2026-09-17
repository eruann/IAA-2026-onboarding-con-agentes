import pytest

from onboarding.game.points import level_for


@pytest.mark.parametrize(
    ("points", "expected"),
    [(0, "Recién llegado"), (99, "Recién llegado"), (100, "En marcha"), (600, "Referente")],
)
def test_nivel_segun_puntos(points: int, expected: str) -> None:
    assert level_for(points) == expected


def test_puntos_negativos_son_error() -> None:
    with pytest.raises(ValueError):
        level_for(-1)

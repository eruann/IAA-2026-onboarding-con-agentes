import pytest
from sqlalchemy.orm import Session

from onboarding.game.models import Person
from onboarding.game.people import list_people, person_card


@pytest.mark.db
def test_lista_primero_a_los_ingresantes(db_session: Session) -> None:
    db_session.add_all(
        [
            Person(key="t-jefa", name="AAA Jefa", role="Jefa", area="X", is_newcomer=False),
            Person(key="t-nuevo", name="ZZZ Nuevo", role="Analista", area="X", is_newcomer=True),
        ]
    )
    db_session.flush()

    keys = [card.key for card in list_people(db_session)]

    assert keys.index("t-nuevo") < keys.index("t-jefa")
    nuevo = next(card for card in list_people(db_session) if card.key == "t-nuevo")
    assert (nuevo.name, nuevo.role, nuevo.is_newcomer) == ("ZZZ Nuevo", "Analista", True)


def test_la_tarjeta_de_una_persona_tiene_lo_que_muestra_la_interfaz() -> None:
    person = Person(key="k", name="Ana", role="Analista", area="Operaciones", is_newcomer=True)

    assert person_card(person).name == "Ana" and person_card(person).is_newcomer

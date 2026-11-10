# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Las personas de la empresa, para elegir con quién entrar a la interfaz."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from onboarding.db.session import session_scope
from onboarding.game.models import Person
from onboarding.paths import load_data_yaml


@dataclass(frozen=True)
class PersonCard:
    key: str
    name: str
    role: str
    area: str
    is_newcomer: bool


# TODO(experiencia): quién es jefe de quién. Hoy no está en ningún lado: la entrada
# deja tildar "Entrar como jefe". Con PM, sumar el jefe de cada persona a
# data/people.yaml (y su columna en people) para que la entrada lo sepa sola.
def list_people(session: Session | None = None) -> list[PersonCard]:
    """Todas las personas, primero los ingresantes y después por nombre."""
    query = select(Person).order_by(Person.is_newcomer.desc(), Person.name)
    with session_scope(session) as db_session:
        return [person_card(person) for person in db_session.scalars(query)]


def team_for_manager(manager_key: str, session: Session | None = None) -> list[PersonCard]:
    """El equipo declarado para un jefe en people.yaml, en orden de la base.

    Si la clave no corresponde a una persona marcada como jefe, devuelve una
    lista vacía. También queda vacía si el jefe todavía no tiene personas a cargo.
    """
    people_data = load_data_yaml("people.yaml")
    is_manager = any(
        person.get("key") == manager_key and person.get("is_manager") is True
        for person in people_data
    )
    if not is_manager:
        return []

    team_keys = {
        person.get("key")
        for person in people_data
        if person.get("manager_key") == manager_key and isinstance(person.get("key"), str)
    }
    if not team_keys:
        return []

    query = (
        select(Person)
        .where(Person.key.in_(team_keys))
        .order_by(Person.is_newcomer.desc(), Person.name)
    )
    with session_scope(session) as db_session:
        manager_exists = db_session.scalar(select(Person.id).where(Person.key == manager_key))
        if manager_exists is None:
            return []
        return [person_card(person) for person in db_session.scalars(query)]


def person_card(person: Person) -> PersonCard:
    return PersonCard(person.key, person.name, person.role, person.area, person.is_newcomer)

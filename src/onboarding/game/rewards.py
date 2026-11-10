# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Catálogo ficticio y canjes. Titular: rol Experiencia.

La integración real con un vendedor de beneficios (Bonda, Betterfly) se diseña,
pero no se conecta en este TP.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from onboarding.db.session import session_scope
from onboarding.game.models import Person, QuestAssignment, QuestRow, Redemption
from onboarding.paths import load_data_yaml


def list_rewards() -> list[dict]:
    """El catálogo de premios de data/rewards.yaml."""
    return load_data_yaml("rewards.yaml", required=True)


def redeem(person_key: str, reward_key: str, session: Session | None = None) -> int:
    """Canjea un premio y devuelve los puntos disponibles que quedan.

    Lanza `ValueError` si la persona o el premio no existen, o si no tiene puntos
    suficientes. La fila de la persona se bloquea durante la operación para que dos
    canjes concurrentes no gasten el mismo saldo.
    """
    rewards_by_key = {reward.get("key"): reward for reward in list_rewards()}
    reward = rewards_by_key.get(reward_key)
    if reward is None:
        raise ValueError(f"No existe el premio '{reward_key}'.")
    cost = reward.get("cost")
    if not isinstance(cost, int) or isinstance(cost, bool) or cost <= 0:
        raise ValueError(f"El premio '{reward_key}' tiene un costo inválido.")

    with session_scope(session, commit=True) as db_session:
        person = db_session.scalar(select(Person).where(Person.key == person_key).with_for_update())
        if person is None:
            raise ValueError(f"No existe la persona '{person_key}'.")

        earned = db_session.scalar(
            select(func.coalesce(func.sum(QuestRow.points), 0))
            .select_from(QuestAssignment)
            .join(QuestRow, QuestAssignment.quest_id == QuestRow.id)
            .where(
                QuestAssignment.person_id == person.id,
                QuestAssignment.status == "approved",
            )
        )
        spent = db_session.scalar(
            select(func.coalesce(func.sum(Redemption.points_spent), 0)).where(
                Redemption.person_id == person.id
            )
        )
        available = earned - spent
        if available < cost:
            raise ValueError(
                f"Puntos insuficientes para '{reward_key}': disponibles {available}, "
                f"necesarios {cost}."
            )

        db_session.add(Redemption(person_id=person.id, reward_key=reward_key, points_spent=cost))
        db_session.flush()
        return available - cost


def redemption_history(person_key: str) -> list[dict]:
    """Canjes de una persona, del más nuevo al más viejo.

    Cada elemento incluye la clave del premio, su título actual en el catálogo,
    los puntos gastados y la fecha de canje en formato ISO.
    """
    with session_scope() as db_session:
        person_id = db_session.scalar(select(Person.id).where(Person.key == person_key))
        if person_id is None:
            return []

        rows = db_session.scalars(
            select(Redemption)
            .where(Redemption.person_id == person_id)
            .order_by(Redemption.created_at.desc(), Redemption.id.desc())
        ).all()

    titles = {reward.get("key"): reward.get("title") for reward in list_rewards()}
    return [
        {
            "reward_key": redemption.reward_key,
            "title": titles.get(redemption.reward_key, redemption.reward_key),
            "points_spent": redemption.points_spent,
            "created_at": redemption.created_at.isoformat(),
        }
        for redemption in rows
    ]

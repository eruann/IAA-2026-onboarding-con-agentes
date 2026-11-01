"""Panel del jefe: ver progreso y validar misiones. Titular: rol Experiencia."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from onboarding.db.session import get_session
from onboarding.game.models import Person, QuestAssignment, QuestRow

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["panel"])
DbSession = Annotated[Session, Depends(get_session)]

# Lo que ve el jefe en la columna Estado. Solo se listan estos dos: lo aprobado o
# rechazado ya no necesita nada de su parte.
STATUS_LABELS = {
    "submitted": "Esperando aprobación",
    "pending": "Pendiente",
}


@router.get("/panel", response_class=HTMLResponse)
# recorrido: panel-jefe
def panel_home(request: Request, session: DbSession) -> HTMLResponse:
    # pending: el ingresante todavía no la hizo. submitted: entregó la evidencia y
    # espera que la aprueben; van primero porque son las que el jefe tiene que mover.
    people = session.scalars(
        select(Person).where(Person.is_newcomer.is_(True)).order_by(Person.name)
    ).all()
    assignments = session.execute(
        select(QuestAssignment, Person.name, QuestRow.title)
        .join(Person, QuestAssignment.person_id == Person.id)
        .join(QuestRow, QuestAssignment.quest_id == QuestRow.id)
        .where(
            Person.is_newcomer.is_(True),
            QuestAssignment.status.in_(STATUS_LABELS),
        )
        .order_by(
            case((QuestAssignment.status == "submitted", 0), else_=1),
            Person.name,
            QuestRow.title,
        )
    ).all()
    pending = [
        {
            "person": person_name,
            "quest": quest_title,
            "status": STATUS_LABELS[assignment.status],
        }
        for assignment, person_name, quest_title in assignments
    ]
    return templates.TemplateResponse(
        request=request,
        name="panel/index.html",
        context={"pending": pending, "people": people},
    )

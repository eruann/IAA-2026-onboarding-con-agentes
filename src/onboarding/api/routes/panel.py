"""Panel del jefe: ver progreso y validar misiones. Titular: rol Experiencia."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from onboarding.db.session import get_session
from onboarding.game.models import Person, QuestAssignment, QuestRow

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["panel"])
DbSession = Annotated[Session, Depends(get_session)]


@router.get("/panel", response_class=HTMLResponse)
# recorrido: panel-jefe
def panel_home(request: Request, session: DbSession) -> HTMLResponse:
    # Las asignaciones en estado pending son misiones todavía no completadas.
    people = session.scalars(
        select(Person).where(Person.is_newcomer.is_(True)).order_by(Person.name)
    ).all()
    assignments = session.execute(
        select(QuestAssignment, Person.name, QuestRow.title)
        .join(Person, QuestAssignment.person_id == Person.id)
        .join(QuestRow, QuestAssignment.quest_id == QuestRow.id)
        .where(Person.is_newcomer.is_(True), QuestAssignment.status == "pending")
        .order_by(Person.name, QuestRow.title)
    ).all()
    pending = [
        {"person": person_name, "quest": quest_title, "status": assignment.status}
        for assignment, person_name, quest_title in assignments
    ]
    return templates.TemplateResponse(
        request=request,
        name="panel/index.html",
        context={"pending": pending, "people": people},
    )

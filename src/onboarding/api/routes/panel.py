# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Panel del jefe: ver progreso y validar misiones. Titular: rol Experiencia."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from onboarding.db.session import get_session
from onboarding.game import STATUS_LABELS, manager_board

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["panel"])
DbSession = Annotated[Session, Depends(get_session)]


@router.get("/panel", response_class=HTMLResponse)
# recorrido: panel-jefe
def panel_home(request: Request, session: DbSession) -> HTMLResponse:
    # Primero lo que el jefe tiene que mover (evidencia entregada), después lo que
    # el ingresante todavía no hizo (ver game.manager_board)
    board = manager_board(session)
    pending = [
        {"person": item.person, "quest": item.quest, "status": STATUS_LABELS[item.status]}
        for item in board.pending
    ]
    return templates.TemplateResponse(
        request=request,
        name="panel/index.html",
        context={"pending": pending, "people": board.newcomers},
    )

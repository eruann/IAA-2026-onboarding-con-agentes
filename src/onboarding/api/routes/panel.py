"""Panel del jefe: ver progreso y validar misiones. Titular: rol Experiencia."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["panel"])


@router.get("/panel", response_class=HTMLResponse)
def panel_home(request: Request) -> HTMLResponse:
    # TODO(experiencia): listar ingresantes, su progreso y las misiones
    # pendientes de aprobación, con botón de aprobar (HTMX, sin recargar).
    return templates.TemplateResponse(
        request=request,
        name="panel/index.html",
        context={"pending": [], "people": []},
    )

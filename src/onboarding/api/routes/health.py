"""Chequeos de salud. Los usa Render para saber si el deploy quedó bien."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from onboarding.db.session import get_session

router = APIRouter(tags=["health"])

# Sesión inyectada por FastAPI: una por request, cerrada al terminar.
DbSession = Annotated[Session, Depends(get_session)]


@router.get("/health")
def health() -> dict[str, str]:
    """Vivo. No toca la base: sirve para saber si el proceso levantó."""
    return {"status": "ok"}


@router.get("/health/db")
def health_db(session: DbSession) -> dict[str, str]:
    """Vivo y con base usable, incluida la extensión pgvector."""
    try:
        version = session.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar()
    except Exception as exc:  # noqa: BLE001 - queremos el detalle en el health
        raise HTTPException(status_code=503, detail=f"base inaccesible: {exc}") from exc

    if version is None:
        raise HTTPException(status_code=503, detail="falta la extensión vector")
    return {"status": "ok", "pgvector": version}

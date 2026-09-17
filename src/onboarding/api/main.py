"""Aplicación única: API + panel del jefe + endpoint de Slack.

Un solo proceso y un solo contenedor en producción. Slack entra por Events API
(HTTP), así que no hace falta un worker aparte.
"""

import logging

from fastapi import FastAPI

from onboarding.api.routes import health, panel
from onboarding.config import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    app = FastAPI(title="Onboarding gamificado con agentes", version="0.1.0")
    app.include_router(health.router)
    app.include_router(panel.router)

    if settings.slack_enabled:
        from onboarding.bot.router import router as slack_router

        app.include_router(slack_router)
    else:
        # Sin tokens la app arranca igual: quien no trabaja en el bot no
        # necesita una app de Slack para levantar el proyecto.
        logger.warning("Slack deshabilitado: faltan SLACK_BOT_TOKEN y SLACK_SIGNING_SECRET")

    return app


app = create_app()

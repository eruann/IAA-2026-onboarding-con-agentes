"""Montaje de Slack dentro de FastAPI: un solo endpoint para todo.

Ahí entran eventos, slash commands y clics en botones. La Request URL que se
carga en la app de Slack es https://<host>/slack/events
"""

from fastapi import APIRouter, Request
from slack_bolt.adapter.fastapi import SlackRequestHandler

from onboarding.bot.app import get_slack_app

router = APIRouter(tags=["slack"])


@router.post("/slack/events")
async def slack_events(request: Request):
    return await SlackRequestHandler(get_slack_app()).handle(request)

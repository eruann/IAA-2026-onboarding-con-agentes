"""App de Bolt en modo Events API.

`process_before_response=True` es obligatorio en este modo: Bolt corre el
listener antes de responderle a Slack. Como Slack corta a los 3 segundos, todo
lo lento (RAG + modelo) va en un listener lazy que responde después por
`say` o `response_url`.
"""

from functools import lru_cache

from slack_bolt import App

from onboarding.config import get_settings


@lru_cache
def get_slack_app() -> App:
    settings = get_settings()
    if not settings.slack_enabled:
        raise RuntimeError("Faltan SLACK_BOT_TOKEN y SLACK_SIGNING_SECRET")

    app = App(
        token=settings.slack_bot_token.get_secret_value(),
        signing_secret=settings.slack_signing_secret.get_secret_value(),
        process_before_response=True,
    )

    from onboarding.bot.handlers import register_handlers

    register_handlers(app)
    return app

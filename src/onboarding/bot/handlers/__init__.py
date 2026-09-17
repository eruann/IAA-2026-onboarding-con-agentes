"""Handlers de Slack, agrupados por tema."""

from slack_bolt import App

from onboarding.bot.handlers import approvals, questions, quests


def register_handlers(app: App) -> None:
    quests.register(app)
    questions.register(app)
    approvals.register(app)

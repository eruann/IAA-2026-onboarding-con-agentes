"""Comandos de misiones: ver las propias, entregar evidencia."""

from slack_bolt import App


def register(app: App) -> None:
    @app.command("/misiones")
    def list_quests(ack, respond, command):
        # ack() primero y siempre: Slack corta a los 3 segundos.
        ack()
        # TODO(experiencia): traer las misiones de la persona con game/ y
        # responder con Block Kit (título, puntos, botón "entregar evidencia").
        respond("Todavía no hay misiones cargadas. (TODO experiencia)")

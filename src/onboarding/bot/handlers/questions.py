"""Preguntas libres del ingresante: mención al bot o mensaje directo."""

from slack_bolt import App


def register(app: App) -> None:
    @app.event("app_mention")
    def on_mention(event, say, ack):
        ack()
        # TODO(experiencia + agentes): mandar el texto al grafo con
        # intent="answer_question" y responder citando la fuente.
        # El trabajo pesado va en un listener lazy: acá solo se acusa recibo.
        say("Estoy leyendo la documentación... (TODO agentes)")

    @app.event("message")
    def on_direct_message(event, say, ack):
        ack()
        if event.get("channel_type") != "im":
            return
        say("Te leo. Todavía no sé responder. (TODO agentes)")

"""Aprobación de misiones por el jefe, con un clic."""

from slack_bolt import App


def register(app: App) -> None:
    @app.action("approve_quest")
    def approve(ack, body, respond):
        ack()
        # TODO(experiencia): marcar aprobada con game/, sumar puntos y disparar
        # la extracción de conocimiento sobre el hilo de la conversación.
        # Registrar quién aprobó y cuándo: es la métrica de horas-persona.
        respond("Aprobación registrada. (TODO experiencia)")

"""Consultas al grafo. Es lo que alimenta las misiones y las derivaciones."""


def who_knows_about(topic: str, limit: int = 3) -> list[str]:
    """Personas que saben de un tema, de más a menos respaldo.

    Lo usa el agente cuando no hay soporte documental: en vez de inventar,
    responde "no tengo esta información, preguntale a X".
    """
    # TODO(grafo): consulta sobre nodes/edges.
    raise NotImplementedError("TODO(grafo): consulta del grafo")

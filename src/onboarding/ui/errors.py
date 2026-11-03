# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Errores explicados en castellano, para mostrar en pantalla.

Se reconocen por el nombre de la clase y no importando el SDK del proveedor:
la interfaz no sabe qué cliente hay detrás de `get_chat_model()`.
"""

from nicegui import ui

from onboarding.paths import repo_relative


def _where(error: BaseException) -> str:
    """Archivo, línea y función donde se lanzó el error (el TODO a completar)."""
    tb = error.__traceback__
    if tb is None:
        return ""
    while tb.tb_next:
        tb = tb.tb_next
    code = tb.tb_frame.f_code
    return f"{repo_relative(code.co_filename)}:{tb.tb_lineno} ({code.co_name})"


# recorrido: errores-en-castellano
def explain(error: BaseException) -> tuple[str, str]:
    """(tipo, mensaje). tipo: "pending" si es un TODO, "error" si falló algo."""
    if isinstance(error, NotImplementedError):
        if "structured_output" in str(error):
            return "error", "Este modelo no sabe devolver salida estructurada. Probá con otro."
        return "pending", f"Todavía no está implementado: {error}. Se completa en {_where(error)}."

    # LangChain a veces les antepone el proveedor (OpenAIRateLimitError)
    name = type(error).__name__.removeprefix("OpenAI")
    detail = str(error)
    if name == "AuthenticationError":
        return "error", "La API key no es válida. Revisá OPENROUTER_API_KEY en el .env."
    if name == "PermissionDeniedError" and "limit" in detail.lower():
        return (
            "error",
            "La key no tiene saldo para este modelo. Elegí uno gratis (los que terminan en :free).",
        )
    if name == "RateLimitError":
        return (
            "error",
            "El modelo está saturado o llegaste al límite de uso gratis. "
            "Probá otro modelo o esperá un minuto.",
        )
    if name == "NotFoundError":
        return "error", "El proveedor no encuentra ese modelo. Elegí otro de la lista."
    if name in {"APIConnectionError", "ConnectError", "ConnectionError"}:
        return (
            "error",
            "No se pudo conectar con el proveedor del modelo. Si es Ollama, ¿está abierto?",
        )
    return "error", f"{name}: {detail[:300]}"


def render_error(error: BaseException) -> None:
    """El error explicado: en naranja si es algo pendiente (un TODO), en rojo si falló."""
    kind, message = explain(error)
    color = "text-orange-9" if kind == "pending" else "text-negative"
    ui.label(message).classes(f"{color} whitespace-pre-wrap")

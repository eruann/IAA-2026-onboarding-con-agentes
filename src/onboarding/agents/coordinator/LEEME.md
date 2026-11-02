# Taller del coordinador

**Nodo:** `agents/coordinator/node.py`. Decide a qué agente va cada mensaje.

Hoy es tonto a propósito: si el mensaje trae un agente elegido (los talleres lo
hacen) lo respeta; si no, todo va a Conocimiento. En este taller el chat **no**
elige agente, así se ve qué decide el coordinador.

## Qué falta

- Sin agente elegido, clasificar el mensaje con el modelo usando la
  `description` de cada agente del registro (`agents/registry.py`).
- Un set fijo de mensajes con el agente esperado, para medirlo igual que el RAG.

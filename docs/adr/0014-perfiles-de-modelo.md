# 0014 — Perfiles de modelo: cada tarea pide lo que necesita

- Fecha: 2026-11-04
- Estado: aceptada
- Decide: Tech Lead

## Contexto

Todo el grafo usaba un solo modelo: el del `.env` o el elegido en el selector. El
agente de Grafo hace dos llamadas distintas: extraer relaciones (salida
estructurada, con un pedido largo) y contestarle a la persona (texto). La primera
necesita un modelo que soporte salida estructurada; la segunda puede ser uno chico
y rápido. Configurar un modelo por tarea no escala: cada tarea nueva sería otra
entrada en el `.env`, con su nombre interno. Además, RAG va a necesitar un modelo
de embeddings (ADR 0005), que tiene otra interfaz y otro proveedor.

## Decisión

Cada tarea pide el modelo por **perfil**, según lo que necesita, y la
configuración dice qué modelo cubre cada perfil:

- **principal** (`get_chat_model`, `LLM_MODEL`): conversar.
- **estructurado** (`get_structured_model`, `LLM_STRUCTURED_MODEL`): devolver datos
  con forma fija. Vacío, usa el principal que se esté usando.
- **embeddings** (`get_embeddings`): textos a vectores. Uno solo para todo el
  sistema; el modelo lo elige el ADR 0005 (hoy, pendiente).

Los agentes reciben sus modelos en `Models` (`main`, `structured`). Los talleres
tienen un segundo selector, «Modelo para datos estructurados»; las pantallas de
Empleado y Jefe solo el principal (el estructurado sale de la configuración). Un
perfil nuevo se suma con un ADR, no por tarea.

## Consecuencias

- Una tarea nueva que devuelve datos con forma fija declara el perfil y queda
  cubierta, sin tocar la configuración.
- Sin `LLM_STRUCTURED_MODEL`, todo funciona como antes: un solo modelo.
- La firma de los agentes cambia: `make_<nodo>(models)` en vez de
  `make_<nodo>(model)`.
- Todavía no se avisa si el modelo elegido para el perfil estructurado no soporta
  salida estructurada: falla al usarlo, con el error del proveedor.

## Alternativas descartadas

- **Un modelo por tarea en la configuración** (`LLM_TASK_MODELS` con el nombre de
  cada tarea): no escala y obliga a conocer los nombres internos.
- **El modelo escrito en cada `prompt.md`:** depende del entorno (Ollama en local,
  OpenRouter en Render) y no debería quedar fijo en el repo.
- **Embeddings como un perfil de chat más:** otra interfaz, otro proveedor
  (OpenRouter no los ofrece) y no se pueden cambiar en vivo sin reindexar.

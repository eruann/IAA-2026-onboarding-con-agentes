# Decisiones de arquitectura (ADR)

Un archivo por decisión, numerado, de una página, con fecha y motivo. Sirve para
dos cosas: que en noviembre nadie tenga que recordar por qué se eligió algo, y
que el informe final se arme copiando estos archivos.

**No se editan una vez aceptados.** Si la decisión cambia, se escribe un ADR
nuevo y se marca el anterior como reemplazado.

Estados: `propuesta` → `aceptada` → `reemplazada por 000X`.

| # | Decisión | Estado |
|---|---|---|
| [0001](0001-stack.md) | Stack: Python, LangGraph, Postgres + pgvector, Slack | aceptada |
| [0002](0002-estructura-monorepo.md) | Monorepo, un paquete por área, una imagen Docker | aceptada |
| [0003](0003-slack-events-api.md) | Slack por Events API en vez de Socket Mode | aceptada |
| [0004](0004-deploy-render-neon.md) | Deploy en Render + Neon | aceptada |
| [0005](0005-embeddings.md) | Modelo de embeddings | **abierta** |
| [0006](0006-llm-via-openrouter.md) | Acceso a modelos vía OpenRouter | aceptada |
| [0007](0007-knowledge-layer.md) | Knowledge layer: documentos y red informal detrás de una sola puerta | aceptada |

Plantilla: [_plantilla.md](_plantilla.md)

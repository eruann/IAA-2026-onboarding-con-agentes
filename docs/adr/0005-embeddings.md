# 0005 — Modelo de embeddings

- Fecha: pendiente
- Estado: **abierta**
- Decide: titular de RAG y evaluación, en su primer PR

## Contexto

El retrieval necesita embeddings del corpus. La decisión define la **dimensión
del vector**, o sea la tabla de chunks: no se puede crear esa tabla antes de
elegir, y cambiar después obliga a reindexar todo.

OpenRouter, que es por donde pasan los modelos de chat (ADR 0006), **no ofrece
embeddings**: esto se resuelve aparte.

## Opciones

| Opción | A favor | En contra |
|---|---|---|
| Modelo local en el contenedor (multilingüe) | costo cero, sin API key para nadie, funciona offline | imagen Docker bastante más pesada, más lento sin GPU |
| API de pago (Voyage, OpenAI) | mejor calidad, rápido, imagen liviana | otra API key y otro costo, además del modelo de chat |

## Criterio de decisión

Medir, no elegir por gusto: correr el set fijo de `eval/rag_questions.yaml` y
comparar recall del retrieval y latencia de la ingesta. El corpus está en
español, así que el modelo tiene que ser multilingüe o específico de español.

## Qué escribir cuando se cierre

Modelo elegido, dimensión, costo estimado de indexar el corpus completo, y qué
hay que hacer para reindexar si más adelante se cambia.

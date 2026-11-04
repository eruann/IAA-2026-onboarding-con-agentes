# 0005 — Modelo de embeddings

- Fecha: 2026-11-04
- Estado: **cerrada**
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

## Decisión

Modelo local, vía `fastembed` (ONNX, sin torch): **no hace falta ninguna API
key y la imagen de Docker crece poco** (~150 MB, sin GPU), en línea con el
resto del proyecto (todo gratis por default, cada key es de cada uno).

El candidato inicial, `intfloat/multilingual-e5-small`, no está en el
registro de modelos que trae esta versión de `fastembed` (sí
`multilingual-e5-large`, pero es 1024 dim — mucho más pesado de lo que pide
este corpus). Elegido en su lugar:
**`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`** —
384 dimensiones, multilingüe, el liviano estándar para similitud semántica. A
diferencia de los modelos `e5` no necesita prefijos distintos para preguntas
y documentos.

**Medido** contra las 28 preguntas de `eval/rag_questions.yaml` (taller RAG,
"Evaluar la búsqueda", k=5), sobre el corpus completo (25 documentos, 154
fragmentos cortando por `##`, issue #16):

- **Recall@5: 92% (23/25)** de las preguntas con respuesta en el corpus
  trajeron el documento correcto entre los 5 resultados.
- **Precisión@5: 34%** de los fragmentos que trajo, en promedio, eran del
  documento correcto (preguntas con `k=5` de documentos cortos devuelven
  fragmentos de otros documentos, que no cuentan como error de recall).
- Las dos preguntas que fallan: `organigrama-001` (trae `tesoreria.md` antes
  que `organigrama.md`: la pregunta "¿Quién es el Jefe de Compras?" se parece
  semánticamente a varios fragmentos de puestos en otros documentos) y
  `bienvenida-001` (sobre un sitio específico de la empresa, mal cubierto por
  el fragmento más corto del documento).
- Las 3 preguntas sin respuesta en el corpus no se cuentan para el recall; el
  retrieval igual trae fragmentos (el agente tiene que derivar en vez de
  usarlos para inventar una respuesta).

**Costo de indexar:** una sola corrida de `ingest_directory` sobre los 25
documentos, ~154 fragmentos, corre en unos segundos en CPU sin GPU (más la
descarga única del modelo, ~130 MB, cacheada después en
`~/.cache/huggingface` dentro del contenedor). Costo en dinero: cero.

**Si se reindexa:** correr de nuevo
`docker compose run --rm app python -m onboarding.knowledge.rag corpus`. Es
idempotente (no reingesta un documento si no cambió) y, si se cambia el
modelo de embeddings a futuro, hay que: 1) actualizar `EMBEDDING_DIM` en
`embeddings.py` si cambia la dimensión, 2) una migración que recree la
columna `embedding` de `chunks` con la nueva dimensión, 3) reingestar todo el
corpus desde cero (`chunks` queda vacía tras la migración, así que no hace
falta borrar nada a mano).

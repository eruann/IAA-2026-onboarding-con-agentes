# 0005 — Modelo de embeddings

- Fecha: 2026-10-12
- Estado: aceptada
- Decide: rol RAG y evaluación

## Contexto

El retrieval necesita embeddings del corpus. La decisión define la **dimensión
del vector**, o sea la tabla de chunks: no se puede crear esa tabla antes de
elegir, y cambiar después obliga a reindexar todo.

OpenRouter, que es por donde pasan los modelos de chat (ADR 0006), **no ofrece
embeddings**: esto se resuelve aparte.

El corpus está en español, así que el modelo tiene que ser multilingüe o
específico de español — no alcanza con un modelo entrenado solo en inglés.

## Decisión

**`bge-m3` servido por Ollama**, usando el perfil `local-llm` que ya existe en
`docker-compose.yml` (el mismo contenedor que ya se usaba para el chat vía
`LLM_PROVIDER=openai_compat`). Se accede con `OpenAIEmbeddings` de
`langchain-openai` — librería que **ya es dependencia del proyecto**, apuntando
a la misma `base_url` que el modelo de chat local.

**Dimensión del vector: 1024.**

No se agrega ninguna dependencia nueva al `pyproject.toml`, y la imagen de la
app no crece: el modelo pesado vive en el contenedor aparte de Ollama
(opcional, se levanta solo si se necesita), no adentro del contenedor de la
app.

`bge-m3` es multilingüe de origen (entrenado para más de 100 idiomas, con
foco explícito en recuperación cross-lingual) — no es un modelo en inglés con
soporte parcial para otros idiomas.

## Consecuencias

- Costo cero, sin API key para nadie, funciona offline una vez bajado el
  modelo (`docker compose exec ollama ollama pull bge-m3`).
- Consistente con el resto del proyecto: igual que `LLM_PROVIDER=fake` es el
  default para no gastar salvo que haga falta, acá se elige la opción sin
  costo como punto de partida.
- Reutiliza infraestructura y dependencias que ya existían — no hay nada nuevo
  que mantener.
- **Lo que no se hizo, con honestidad:** el criterio original pedía medir
  recall comparando contra una API de pago (Voyage/OpenAI). Eso no se hizo —
  habría que pagar por una key solo para la comparación, y el proyecto
  prioriza costo cero salvo necesidad real. Lo que sí se mide es el recall
  **real** de `bge-m3` contra el set fijo de `eval/rag_questions.yaml`, una
  vez que la ingesta y el retriever estén implementados. Si ese recall sale
  pobre, la alternativa a probar primero es la API de pago — no antes.
- Más lento que una API sin GPU — aceptable para el volumen de este proyecto
  (16 documentos), a revisar si el corpus creciera mucho.
- Reindexar todo el corpus implica volver a embeber cada chunk — con 16
  documentos de este tamaño, es una operación de segundos, no un problema.

## Alternativas descartadas

- **Librería de embeddings (ej. `sentence-transformers`) instalada dentro del
  contenedor de la app:** descartada porque infla la imagen de la app con
  pesos de modelo y dependencias de ML que solo hacen falta para esta tarea
  puntual — correrlo en el contenedor aparte de Ollama evita ese problema.
- **`nomic-embed-text`:** también multilingüe y más liviano, alternativa
  razonable — descartada por ahora porque `bge-m3` tiene mejor desempeño
  documentado específicamente en benchmarks multilingües/cross-lingual. Se
  puede reconsiderar si el recall medido no es bueno.
- **API de pago (Voyage, OpenAI):** descartada por costo, no por calidad —
  sigue siendo la opción de respaldo si el recall local no alcanza.

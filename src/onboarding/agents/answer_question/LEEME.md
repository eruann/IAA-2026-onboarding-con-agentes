> **andamiaje**
>
> Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
> construya, pruebe o entienda el producto (talleres, diagramas, guías).
> No es parte del producto.

# Taller RAG y evaluación

**Tu parte:** lo escrito. Que el bot encuentre el documento y la sección que
responden cada pregunta, y medir qué tan bien lo hace.

## Qué construís y qué trae el taller

**Lo construís vos:** tu agente (`node.py` y `prompt.md`, en esta carpeta) y lo
escrito, en `knowledge/rag/` (producto):

- `chunking.py` → `chunk_text`: corta un documento en fragmentos, respetando
  los títulos `##` (issue #16 cerrado: cada fragmento sabe su sección, nunca
  mezcla dos). **Ya funciona.**
- `models.py`: tablas `documents` y `chunks`, con el vector de 384 dimensiones
  de `embeddings.py`. **Ya funciona** (migración `0004`).
- `embeddings.py` → `embed_texts`: [ADR 0005](../../../../docs/adr/0005-embeddings.md)
  cerrada — modelo local (`paraphrase-multilingual-MiniLM-L12-v2` vía
  `fastembed`, sin API key, 384 dim). **Ya funciona.**
- `ingest.py` → `ingest_directory`: corta el corpus, calcula embeddings y
  guarda en pgvector; idempotente (no reingesta un documento si no cambió, y
  borra los fragmentos viejos si cambió). **Ya funciona.**
- `retriever.py` → `retrieve`: búsqueda por similitud de coseno en pgvector.
  **Ya funciona.**
- `citations.py` → `quote_is_supported`: verifica que una cita esté textual.
  **Ya funciona.**

**Lo trae el taller** (`workshop.py`, en esta carpeta): el chat con tu agente y las
pruebas, en las tres secciones de siempre. Las de la knowledge layer
(`retrieve`, `quote_is_supported`) se llaman desde ahí; las pruebas ad hoc para
mirar y medir tu trabajo están en `checks.py`:

- `chunk_document`: muestra cómo corta `chunk_text` un documento del corpus.
- `evaluate_retrieval`: corre las preguntas de `eval/rag_questions.yaml` contra
  `retrieve` y calcula recall y precisión.

No hace falta tocarlas para avanzar. Si cambiás lo que devuelve `chunk_text` o
`retrieve`, ajustalas (tienen su test en `checks_test.py`).

## Qué falta

El primer PR del rol (ADR 0005, tablas, ingesta de punta a punta, `retrieve()`
e [issue #16](https://github.com/eruann/IAA-2026-onboarding-con-agentes/issues/16))
ya está. Lo que sigue:

1. `evaluate_retrieval` mide el documento, no la sección: ahora que cada
   fragmento guarda su sección, se puede medir también si trajo la sección
   esperada (`expected_section` ya está en `eval/rag_questions.yaml`, solo
   falta usarlo).
2. `answer_question` (`node.py`) todavía no usa `retrieve`: responde con dos
   documentos fijos metidos enteros en el prompt. Conectarlo es el siguiente
   paso (ver `AGENTS.md`, rol Agentes y orquestación, o pedí un plan para
   esto).
3. Estimación de tokens y costo por ingresante (con los datos de `llm_calls`).
4. Afinar precisión@5 (hoy 34%, ver el ADR 0005 cerrado): probar otro `k`,
   otro tamaño de fragmento, o filtrar resultados por un piso de similitud.

## Qué probar en el taller

- **Ver cómo se corta un documento**: elegí `tesoreria.md` y mirá la columna
  *sección*: cada fragmento tiene una sola (issue #16 cerrado). Probá con
  otros tamaños y solape.
  Mirá también la columna *caracteres*: en `glosario.md` y `tesoreria.md` hay
  fragmentos de más de `max_chars` (hasta ~2000 con el tamaño por defecto). Un
  párrafo largo que llega cuando ya hay un fragmento empezado no se corta.
- **Buscar en el corpus**: probá preguntas del set de evaluación y mirá si
  trae el documento y la sección correctos. Necesita el corpus ingestado
  (`docker compose run --rm app python -m onboarding.knowledge.rag corpus`).
- **Evaluar la búsqueda**: tu número principal. Recall@k es en cuántas preguntas
  trajo el documento correcto; precisión@k, cuánto de lo que trajo era de ese
  documento. Las preguntas sin respuesta no cuentan: ahí el agente tiene que
  derivar. Hoy: Recall@5 92%, Precisión@5 34% (ver el ADR 0005 cerrado para el
  detalle). Corrélo antes y después de cada cambio (tamaño de fragmento,
  modelo de embeddings, `k`) y anotá los números en el PR.
- **Verificar una cita**: pegá una frase y el texto de un documento. Es el
  control que evita que el bot cite algo que no está.
- **Chat**: el agente de conocimiento (`answer_question`). Por ahora sigue
  respondiendo con dos documentos fijos enteros (`node.py` todavía no usa
  `retrieve`, ver "Qué falta").

El set de preguntas (`eval/rag_questions.yaml`) se copia a la imagen al
construirla: si lo cambiás, `docker compose up --build`.

## Pedidos de plan para Claude Code o Codex

Prendé el modo plan (Claude Code: `Shift+Tab` hasta *plan mode*; Codex:
`/plan`; más detalle en `DEVELOPMENT.md`, "Primero el plan") y pedí, por
ejemplo:

- `Armame un plan para decidir el modelo de embeddings del ADR 0005. ¿Qué opciones hay y cómo las comparo con evaluate_retrieval?`
- `Armame un plan para crear las tablas documents y chunks con su migración. Explicame cada columna.`
- `Armame un plan para implementar retrieve() con pgvector. ¿Cómo funciona la búsqueda por similitud?`
- `Armame un plan para el issue #16: cortar por títulos ## y guardar la sección. ¿Qué cambia en chunk_text y en sus tests?`

Leé el plan, preguntá lo que no entiendas y recién ahí aprobalo.

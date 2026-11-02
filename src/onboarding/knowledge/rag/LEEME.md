> **andamiaje**
>
> Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
> construya, pruebe o entienda el producto (talleres, diagramas, guías).
> No es parte del producto.

# Taller RAG y evaluación

**Tu parte:** lo escrito. Que el bot encuentre el documento y la sección que
responden cada pregunta, y medir qué tan bien lo hace.

## Qué construís y qué trae el taller

**Lo construís vos** (todo en `knowledge/rag/`):

- `chunking.py` → `chunk_text`: corta un documento en fragmentos. **Ya
  funciona**, pero por párrafos y sin mirar los títulos `##` (ver más abajo).
- `models.py`: tablas `documents` y `chunks`. Pendiente.
- `embeddings.py` → `embed_texts`: pendiente. Antes, decidir el modelo de
  embeddings en el [ADR 0005](../../../../docs/adr/0005-embeddings.md).
- `ingest.py` → `ingest_directory`: lee y corta el corpus; falta guardar en
  pgvector.
- `retriever.py` → `retrieve`: la búsqueda. Pendiente.
- `citations.py` → `quote_is_supported`: verifica que una cita esté textual.
  **Ya funciona.**

**Lo trae el taller** (`knowledge/rag/workshop.py`): la declaración de las
pruebas y dos ayudas para mirar y medir tu trabajo:

- `chunk_document`: muestra cómo corta `chunk_text` un documento del corpus.
- `evaluate_retrieval`: corre las preguntas de `eval/rag_questions.yaml` contra
  `retrieve` y calcula recall y precisión.

No hace falta tocarlas para avanzar. Si cambiás lo que devuelve `chunk_text` o
`retrieve`, ajustalas (tienen su test en `workshop_test.py`).

## Qué falta

1. ADR 0005: elegir el modelo de embeddings, midiendo, no por gusto.
2. Tablas `documents` y `chunks` con su migración.
3. Ingesta de punta a punta: cortar, calcular embeddings y guardar, sin
   duplicar si se corre dos veces.
4. `retrieve()`: búsqueda por similitud en pgvector.
5. [Issue #16](https://github.com/eruann/IAA-2026-onboarding-con-agentes/issues/16):
   cortar respetando los títulos `##` y guardar la sección de cada fragmento.
   Con eso se puede medir también la sección correcta.

## Qué probar en el taller

- **Ver cómo se corta un documento**: elegí `tesoreria.md` y mirá la columna
  *títulos ## adentro*: cuando un fragmento tiene varios, mezcla secciones (el
  issue #16). Probá con otros tamaños y solape, y volvé a mirar después de
  cambiar `chunk_text`.
  Mirá también la columna *caracteres*: en `glosario.md` y `tesoreria.md` hay
  fragmentos de más de `max_chars` (hasta ~2000 con el tamaño por defecto). Un
  párrafo largo que llega cuando ya hay un fragmento empezado no se corta.
- **Buscar en el corpus**: aparece como pendiente hasta que exista `retrieve`.
  Después, probá preguntas del set de evaluación y mirá si trae el documento y la
  sección correctos.
- **Evaluar la búsqueda**: tu número principal. Recall@k es en cuántas preguntas
  trajo el documento correcto; precisión@k, cuánto de lo que trajo era de ese
  documento. Las preguntas sin respuesta no cuentan: ahí el agente tiene que
  derivar. Corrélo antes y después de cada cambio (tamaño de fragmento, modelo de
  embeddings, `k`) y anotá los números en el PR.
- **Verificar una cita**: pegá una frase y el texto de un documento. Es el
  control que evita que el bot cite algo que no está.
- **Chat**: el agente de conocimiento (`answer_question`). Hoy responde con dos
  documentos enteros; cuando use `retrieve`, va a responder con lo que encuentre
  tu búsqueda.

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

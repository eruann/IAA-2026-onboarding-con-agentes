# Taller RAG: lo escrito

**Tu agente:** Conocimiento (`agents/answer_question/node.py`). Responde dudas
citando documento y sección; si no hay respaldo, deriva con `who_knows_about`.

**Tu parte de la knowledge layer:** `knowledge/rag/` (ingesta, embeddings,
búsqueda y verificación de citas).

## Qué falta

1. Decidir el modelo de embeddings (`docs/adr/0005-embeddings.md`) y crear las
   tablas `documents` y `chunks` (`knowledge/rag/models.py`).
2. Cortar el corpus por secciones `##` y guardar la sección de cada fragmento
   (issue #16).
3. `retrieve()` en `knowledge/rag/retriever.py`: hoy está pendiente.
4. El agente Conocimiento usando `retrieve`, `quote_is_supported` y
   `who_knows_about`.

## Cómo probar

- **Buscar en el corpus**: ves los fragmentos que trae `retrieve`, sin modelo.
- **Evaluar la búsqueda**: corre `eval/rag_questions.yaml` y marca en cuáles
  trajo el documento correcto.
- **El chat** de este taller le habla a tu agente.

## Pedidos listos para Claude Code o Codex

- `Implementá retrieve() en knowledge/rag/retriever.py con pgvector, con su test.`
- `Agregá a mi taller (knowledge/rag/workshop.py) una prueba que muestre los fragmentos de un documento por sección.`
- `Hacé que el agente answer_question use knowledge.retrieve y cite documento y sección, con tests usando el modelo fake.`

# Taller Agentes y orquestación

**Tu agente:** Diseñador de misiones (`agents/generate_quest/node.py`). Propone
misiones nuevas a partir de la documentación de un puesto. Propone: las misiones
del juego las siguen definiendo Experiencia y PM en `data/quests.yaml`.

**Además:** las tools que usan los agentes (`agents/tools.py`), el versionado de
prompts (`agents/prompts/`) y la comparación de modelos por costo y latencia.

## Qué falta

1. El Diseñador usando `knowledge.retrieve` (documentación del puesto) y
   `knowledge.who_knows_about` (a quién involucrar), y devolviendo misiones con
   el formato de `data/quests.yaml`.
2. Las tools de `agents/tools.py`, envolviendo las interfaces públicas de
   `knowledge` y `game`.
3. Comparar dos modelos con el mismo pedido (selector de modelo del taller) y
   registrar costo y latencia.

## Cómo probar

- **El chat** de este taller le habla a tu agente.
- **Ver un prompt**: el texto exacto que recibe el modelo.

## Pedidos listos para Claude Code o Codex

- `Hacé que generate_quest use knowledge.retrieve y devuelva misiones con el formato de data/quests.yaml, con test usando el modelo fake.`
- `Agregá a agents/tools.py una tool buscar_documentacion que envuelva knowledge.retrieve, con su test.`

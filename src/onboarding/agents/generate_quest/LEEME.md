> **andamiaje**
>
> Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
> construya, pruebe o entienda el producto (talleres, diagramas, guías).
> No es parte del producto.

# Taller Diseñador de misiones

**Tu parte:** un agente que propone misiones nuevas para un puesto a partir de
su documentación y de quién sabe qué en la empresa. Propone borradores: cuáles
entran al juego lo deciden Experiencia y PM.

## Qué construís y qué trae el taller

**Lo construís vos** (`agents/generate_quest/`):

- `node.py` → el nodo `generate_quest`. Hoy le pasa el pedido al modelo con su
  prompt y devuelve texto libre.
- `agents/prompts/generate_quest.md`: el prompt, con lo que hace buena a una
  misión.

**Lo usás de otros roles** (por `onboarding.knowledge`):

- `retrieve` (RAG): la documentación del puesto. Pendiente.
- `who_knows_about` (Grafo): a quién involucrar en la misión. Pendiente.

**Lo trae el taller** (`agents/generate_quest/workshop.py`):

- `review_proposal`: revisa misiones propuestas con las mismas reglas que las
  misiones del juego (campos, puntos, quién aprueba) y marca si la `key` ya
  existe.
- La revisión de las misiones actuales, la búsqueda de documentación y "¿Quién
  sabe de?", para probar desde acá lo que usa tu agente.

## Qué falta

1. Que el nodo devuelva las misiones con la forma de `Quest` (`game/quests.py`),
   en el formato de `data/quests.yaml`: `key`, `title`, `description`, `points`,
   `approver` (`manager`, `helpdesk` o `agent`) y `evidence_required`.
2. Que use `retrieve` para leer la documentación del puesto y `who_knows_about`
   para saber a quién involucrar. Mientras no estén, se simulan en los tests.
3. Que respete el criterio del TP: puntos por aprender y recorrer la
   organización, nunca por rendimiento.

## Qué probar en el taller

- **Chat**: pedile misiones para un puesto ("Armame dos misiones para un analista
  de Tesorería"). El panel **Grafo** marca por dónde pasó.
- **Revisar una misión propuesta**: pegá lo que propuso el agente. Acepta el
  bloque ```yaml``` aunque venga con texto alrededor. Cuando sale "✅ Lista",
  ya se la podés pasar a Experiencia y PM.
- **Ver las misiones actuales**: antes de proponer, para no repetir.
- **Buscar documentación del puesto** y **¿Quién sabe de?**: aparecen como
  pendientes hasta que RAG y Grafo las terminen.

## Pedidos de plan para Claude Code o Codex

Prendé el modo plan (Claude Code: `Shift+Tab` hasta *plan mode*; Codex:
`/plan`; más detalle en `DEVELOPMENT.md`, "Primero el plan") y pedí, por
ejemplo:

- `Armame un plan para que generate_quest devuelva misiones con la forma de Quest en YAML. ¿Qué cambia en el prompt y en el nodo?`
- `Armame un plan para que generate_quest use retrieve y who_knows_about. ¿Cómo los simulo en los tests mientras no estén?`
- `¿Qué hace buena a una misión según el prompt y el criterio del TP? Explicámelo sin cambiar nada.`

Leé el plan, preguntá lo que no entiendas y recién ahí aprobalo.

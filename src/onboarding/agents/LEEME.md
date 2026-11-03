> **andamiaje**
>
> Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
> construya, pruebe o entienda el producto (talleres, diagramas, guías).
> No es parte del producto.

# Taller Agentes y orquestación

**Tu parte:** lo que une a los agentes de todos los roles. Cada rol construye su
nodo; vos, el coordinador que decide a cuál va cada mensaje, el grafo que los
conecta, las tools que comparten, los prompts y la comparación de modelos.

El taller tiene dos funciones:

1. **El coordinador**, que es el agente de este taller: el chat habla con él.
2. **Revisar los agentes de los demás roles**: que cada nodo cumpla lo que espera
   el coordinador y que pasar por el coordinador dé lo mismo que ir directo.

## Qué construís y qué trae el taller

**Lo construís vos:**

1. **Coordinador** (`route` en `agents/graph.py`): decide a qué nodo va cada
   mensaje. Hoy es un ruteo por `intent` que elige quien llama (sin `intent`, va
   a `answer_question`); falta que lo decida el coordinador a partir del mensaje.
2. **Grafo y `run_turn`** (`graph.py`, `run.py`, `state.py`): cómo se conectan
   los nodos y la entrada única que usan la interfaz y Slack.
3. **Tools** (`agents/tools.py`): funciones chicas que los agentes pueden
   llamar, envolviendo la interfaz pública de otros módulos
   (`search_documentation`, `who_knows`, `pending_missions`). Hoy son pendientes.
4. **Prompts** (el `prompt.md` de cada agente, cargado con
   `onboarding.llm.load_prompt`): cómo se versionan y cómo se comparan dos
   versiones.
5. **Comparación de modelos**: costo y latencia de cada modelo, con datos. La
   latencia ya se mide en el taller; el costo sale de `llm_calls` cuando se
   guarde.

**Los nodos son de cada rol:**

| Nodo | Rol |
|---|---|
| `answer_question` | RAG y evaluación (con el "no sé, preguntale a X") |
| `validate_evidence` | Experiencia |
| `extract_knowledge` | Grafo cultural y datos |
| `generate_quest` | Diseñador de misiones |

Cada agente vive en su carpeta `agents/<nodo>/` con la misma forma: `node.py`
(con su `NODE`: nombre, título, rol y prompt), `node_test.py` y `prompt.md`. La
lista de agentes está una sola vez, en `NODES` (`agents/graph.py`).

**Lo trae el taller** (`agents/workshop.py`, con las ayudas en `agents/checks.py`):
el chat con el coordinador y estas pruebas:

| Prueba | Para qué |
|---|---|
| Revisar los nodos (`check_nodes`) | Corre cada nodo y revisa que devuelva lo que espera el coordinador: un `dict` con claves del estado, `output` con texto, `citations` como lista de textos y `referred_to` como nombre o `None`. Usa el modelo fake, sin costo, salvo que prendas `use_real_model` |
| ¿A qué nodo iría? (`route_message`) | Qué decide el coordinador con un mensaje, sin correr el nodo |
| Coordinador contra nodo directo (`ab_test`) | Prueba A/B: la misma pregunta por el coordinador y directo a un nodo. Dice si el coordinador eligió el mismo nodo y si las respuestas coinciden. Con la pregunta vacía repite tu último mensaje del chat, con la conversación de antes |
| Preguntarle a un nodo (`ask_node`) | Una pregunta suelta a un nodo, con el recorrido y cuánto tardó. Con «Comparar con otro modelo», dos modelos lado a lado |
| Ver el prompt de un nodo (`show_prompt`) | El `.md` tal como lo recibe el modelo |

## Qué falta

1. Que el coordinador decida el nodo a partir del mensaje (hoy manda todo a
   `answer_question` si nadie pide otro).
2. Las tools de `agents/tools.py`.
3. Comparar modelos por costo: guardar `llm_calls` (hoy el taller mide solo la
   latencia).
4. Versionar los prompts y comparar dos versiones con las preguntas de `eval/`.

## Revisar el trabajo de otro rol

La app lee el código de tu carpeta (Docker monta `src/`) y se recarga sola, así
que el taller prueba la rama en la que estés:

1. Traé el PR o la rama: `gh pr checkout <número>` o `git switch <rama>`.
2. Si trae migraciones: `docker compose run --rm app alembic upgrade head`.
3. En el taller: **Revisar los nodos**, después el chat y **Coordinador contra
   nodo directo** con el nodo de ese rol.
4. Volvé a tu rama: `git switch main`.

## Qué probar en el taller

- **Chat**: escribí como un ingresante. El panel **Grafo** marca a qué nodo lo
  mandó el coordinador y, si falló, en qué nodo.
- **Revisar los nodos**: después de mergear o al revisar el PR de otro rol.
- **Coordinador contra nodo directo**: cuando el coordinador empiece a decidir
  solo, para ver que mande cada pregunta al nodo correcto.
- **Preguntarle a un nodo**: anotá los tiempos cuando compares modelos o prompts.
- **El grafo**: es tu mapa. Si cambiás nodos, flechas o lo que llama cada nodo,
  regenerá `agents/grafo.json`:
  `docker compose run --rm app python -m onboarding.agents.lineage`.

## Pedidos de plan para Claude Code o Codex

Prendé el modo plan (Claude Code: `Shift+Tab` hasta *plan mode*; Codex:
`/plan`; más detalle en `DEVELOPMENT.md`, "Primero el plan") y pedí, por
ejemplo:

- `Armame un plan para que el coordinador decida el nodo a partir del mensaje, sin que lo elija quien llama. ¿Cómo lo pruebo con el modelo fake?`
- `Armame un plan para las primeras tools de agents/tools.py. ¿Cuáles usaría cada nodo?`
- `Armame un plan para versionar los prompts y comparar dos versiones con las preguntas de eval/.`
- `Armame un plan para medir costo y latencia por modelo con llm_calls.`

Leé el plan, preguntá lo que no entiendas y recién ahí aprobalo.

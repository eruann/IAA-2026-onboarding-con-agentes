> **andamiaje**
>
> Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
> construya, pruebe o entienda el producto (talleres, diagramas, guías).
> No es parte del producto.

# Taller Agentes y orquestación

**Tu parte:** lo que une a los agentes de todos los roles. Cada rol construye su
nodo; vos, el coordinador que decide a cuál va cada mensaje, el grafo que los
conecta, las tools que comparten, los prompts y la comparación de modelos.

## Qué construís y qué trae el taller

**Lo construís vos:**

1. **Coordinador** (`agents/graph.py`): decide a qué nodo va cada mensaje. Hoy
   es un ruteo por `intent` que elige quien llama; falta que lo decida el
   coordinador a partir del mensaje.
2. **Grafo y `run_turn`** (`graph.py`, `run.py`, `state.py`): cómo se conectan
   los nodos y la entrada única que usan la interfaz y Slack.
3. **Tools** (`agents/tools.py`): funciones chicas que los agentes pueden
   llamar, envolviendo la interfaz pública de otros módulos (por ejemplo
   `buscar_documentacion`, `quien_sabe_de`, `misiones_pendientes`). Hoy está
   vacío.
4. **Prompts** (`agents/prompts/*.md`, cargados con `onboarding.llm.load_prompt`):
   dónde viven, cómo se versionan y cómo se comparan dos versiones.
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

Cuando un rol empieza su nodo, lo pasa de `nodes.py` a `agents/<nodo>/` (como
`agents/extract_knowledge/`).

**Lo trae el taller** (`agents/workshop.py`): el chat con selector de nodo y dos
pruebas:

- `show_prompt`: el prompt de un nodo tal como lo recibe el modelo.
- `ask_node`: una pregunta suelta a un nodo, con su respuesta, el recorrido y
  cuánto tardó.

## Qué probar en el taller

- **Chat**: elegí el nodo arriba del campo de texto. El panel **Grafo** marca por
  dónde pasó cada mensaje y, si falló, en qué nodo.
- **Preguntarle a un nodo**: con «Comparar con otro modelo» ves dos respuestas
  lado a lado con lo que tardó cada una. Anotá los números cuando compares
  modelos o prompts.
- **Ver el prompt de un nodo**: antes y después de cambiar un prompt.
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

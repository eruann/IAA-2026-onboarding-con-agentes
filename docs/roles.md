# Roles: quién hace qué y por dónde empezar

Los perfiles y sus tareas salen del documento de plataforma y roles del equipo.
Acá está la traducción a carpetas del repo y al primer PR de cada uno.

El titular es responsable de que la tarea **exista y se termine**, no de
ejecutarla solo. El backup la cubre si el titular desaparece una semana.

| # | Perfil | Titular | Backup |
|---|---|---|---|
| 1 | PM / Producto | | |
| 2 | Tech Lead / Plataforma | Matías Rodriguez (@eruann) | |
| 3 | Agentes y orquestación | Matías Rodriguez (@eruann) | |
| 4 | RAG y evaluación | Andrés Salinas (@silo86) | |
| 5 | Grafo cultural y datos | Gabriel Figueiro (@ghfigueiro) | |
| 6 | Experiencia: interfaz y game design | Fausto Baritoli (@faustoabc) | |
| 7 | Diseñador de misiones | | |
| 8 | Comms y entregables (sombrero chico) | | |

## Un agente por rol

Cada rol construye **su agente**, un nodo del grafo de LangGraph, y lo prueba en
su taller de la interfaz web (`/ui`, ver [talleres.md](talleres.md)). Agentes y
orquestación arma lo que los une: el coordinador que decide a qué nodo va cada
mensaje.

| Nodo | Qué hace | Rol |
|---|---|---|
| `answer_question` | Responde con la knowledge layer, citando la fuente; si no hay soporte, deriva ("preguntale a X") | RAG y evaluación |
| `validate_evidence` | Revisa la evidencia que entrega el ingresante para una misión | Experiencia |
| `extract_knowledge` | Saca quién sabe qué de las conversaciones | Grafo cultural y datos |
| `generate_quest` | Propone misiones nuevas a partir de la documentación del puesto | Diseñador de misiones |
| Coordinador | Decide a qué nodo va cada mensaje | Agentes y orquestación |

Cada agente vive en su carpeta `agents/<nodo>/`, siempre con la misma forma:
`node.py`, `node_test.py` y su `prompt.md`. Si entendés uno, entendés los demás
(ver "Cómo está armado cada rol" en `AGENTS.md`).

## 1. PM / Producto

**Carpetas:** `docs/`, `corpus/`, `data/`, `eval/baseline/`

**Primer PR:** elegir empresa ficticia y rubro, y escribir los primeros 5
documentos del corpus. Bloquea a todos los demás: sin corpus no hay RAG, sin
rol definido no hay misiones.

Después: hitos de onboarding que se miden, baseline manual (el mismo proceso
hecho a mano, con horas registradas), calendario y documentos de la cátedra.

## 2. Tech Lead / Plataforma

**Carpetas:** `src/onboarding/db/`, `config.py`, `llm/callbacks.py`,
`Dockerfile`, `docker-compose.yml`, `.github/`, `render.yaml`

**Primer PR:** que `docker compose up` funcione en Linux **y** en Windows, con
alguien de cada sistema confirmándolo.

Después: repo en GitHub con `main` protegida y CODEOWNERS, la demo online
siguiendo [runbooks/deploy.md](runbooks/deploy.md) (Neon, OpenRouter, Render,
Slack), persistir `llm_calls` (costo por corrida), secretos.

## 3. Agentes y orquestación

**Carpetas:** `src/onboarding/agents/` (`graph.py`, `common.py`, `run.py`, `state.py`,
`tools.py`), `llm/factory.py`, `llm/prompts.py`. Los nodos son de cada rol (ver
la tabla de arriba).

Lo que une a los agentes de todos los roles:

1. **Coordinador:** decide a qué nodo va cada mensaje (hoy, un ruteo por
   `intent` que elige quien llama).
2. **Grafo y `run_turn`:** cómo se conectan los nodos y la entrada única que
   usan la interfaz y Slack.
3. **Tools** (`agents/tools.py`): funciones chicas que los agentes pueden
   llamar, envolviendo la interfaz pública de otros módulos.
4. **Prompts:** dónde viven, cómo se cargan y cómo se versionan.
5. **Comparación de modelos:** costo y latencia por modelo, con datos (sale de
   `llm_calls`), para justificar la elección.

**Primer PR:** el coordinador decidiendo el nodo a partir del mensaje, probado
con el modelo fake.

## 4. RAG y evaluación

**Carpetas:** `src/onboarding/knowledge/rag/`, `eval/rag_questions.yaml`

Parte de la knowledge layer: **lo escrito**.

**Su agente:** `answer_question`, que responde citando documento y sección y,
si no hay soporte, deriva con `who_knows_about` ("preguntale a X").

**Primer PR:** decidir el modelo de embeddings (ADR 0005), crear la tabla de
chunks y dejar la ingesta andando de punta a punta.

Después: 15-20 preguntas con respuesta conocida definidas **antes** de correr el
experimento, precisión/recall del retrieval medidos aparte de la calidad de la
respuesta, y estimación de tokens y costo por ingresante.

## 5. Grafo cultural y datos

**Carpetas:** `src/onboarding/knowledge/informal_network/`,
`eval/informal_network_ground_truth.yaml`

Parte de la knowledge layer: **lo no escrito**, la red informal que el
organigrama no muestra (quién sabe de qué, a quién se consulta de verdad).

**Su agente:** `extract_knowledge` (`agents/extract_knowledge/`).

**Primer PR:** tablas `nodes` y `edges` con su migración, y el esquema de
extracción (sujeto, relación, objeto, frase textual de respaldo).

Después: extracción estructurada desde las conversaciones, ground truth del grafo
hecho a mano, métrica de cobertura contra ese ground truth, y las consultas que
alimentan las próximas misiones.

## 6. Experiencia: interfaz y game design

**Carpetas:** `src/onboarding/game/`, `api/`, `bot/`

Dueño del **ciclo de vida de una misión**: qué es una misión (`Quest` y sus
tablas), las 6-8 misiones del TP en `data/quests.yaml` (con PM), asignarlas al
ingresante, la entrega de evidencia, la aprobación del jefe, puntos, niveles,
canje y tono. Las misiones nuevas que propone el Diseñador de misiones entran
solo si Experiencia y PM las aprueban.

**Su agente:** `validate_evidence`, que revisa la evidencia de una misión. La
aprobación final del jefe siempre gana sobre el agente.

**Primer PR:** tablas del juego y panel del jefe mostrando ingresantes y misiones
pendientes.

Después: `/misiones` en Slack, aprobación de un clic, las 6-8 misiones y el
catálogo de canje en `data/`, dial de tono, y la pantalla de transparencia que
le muestra al ingresante qué captura el agente.

## 7. Diseñador de misiones

**Carpetas:** `agents/generate_quest/` (su agente, su prompt y su taller).

**Su agente:** `generate_quest`, que propone misiones nuevas para un puesto a
partir de su documentación (`retrieve`, de RAG) y de quién sabe qué
(`who_knows_about`, de Grafo). Entrega borradores con la forma de `Quest`: no
toca el juego. Cuáles entran a `data/quests.yaml` lo deciden Experiencia y PM.

**Primer PR:** `generate_quest` devolviendo misiones con la forma de `Quest`, que
pasen la revisión de misiones del taller de Experiencia.

## 8. Comms y entregables

**Carpetas:** `docs/minutas/`

Sombrero transversal: lo lleva alguien que ya tiene otro perfil. Canales y
convenciones del Slack del equipo, minuta de 5 líneas después de cada reunión,
deadlines de la cátedra, guion y grabación de la demo final.

## Reparto

Regla acordada: primero se reparten los perfiles que **nadie** eligió en la
encuesta (plataforma y evaluación), y después los que todos quieren. Al revés
queda un agujero. Un perfil sin titular es un perfil que no se hace.

Rotación pactada: en plataforma y evaluación, el backup ejecuta al menos una vez,
para que el conocimiento no quede en una sola cabeza.

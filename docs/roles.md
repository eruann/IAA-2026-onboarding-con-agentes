# Roles: quién hace qué y por dónde empezar

Los perfiles y sus tareas salen del documento de plataforma y roles del equipo.
Acá está la traducción a carpetas del repo y al primer PR de cada uno.

**Cada rol construye su agente** (un nodo del grafo de LangGraph) y lo prueba en
su **taller**, dentro de la interfaz: chat con su agente y pruebas directas de sus
funciones. Qué agente es de quién está en `src/onboarding/agents/registry.py`;
cómo agregar pruebas al taller, en la sección "Agentes y talleres" de
`AGENTS.md`. El porqué, en [ADR 0009](adr/0009-agente-por-rol-y-talleres.md).

| Rol | Agente o nodo | Taller (`workshop.py` + `LEEME.md`) |
|---|---|---|
| Tech Lead | Coordinador (`agents/coordinator/`) | `agents/coordinator/` |
| Agentes y orquestación | Diseñador de misiones (`agents/generate_quest/`) | `agents/` |
| RAG y evaluación | Conocimiento (`agents/answer_question/`) | `knowledge/rag/` |
| Grafo cultural y datos | Red informal (`agents/extract_knowledge/`), nodo final | `knowledge/informal_network/` |
| Experiencia | Mis misiones (`agents/quests/`) | `game/` |

El titular es responsable de que la tarea **exista y se termine**, no de
ejecutarla solo. El backup la cubre si el titular desaparece una semana.

| # | Perfil | Titular | Backup |
|---|---|---|---|
| 1 | PM / Producto | | |
| 2 | Tech Lead / Plataforma | | |
| 3 | Agentes y orquestación | | |
| 4 | RAG y evaluación | | |
| 5 | Grafo cultural y datos | | |
| 6 | Experiencia: interfaz y game design | | |
| 7 | Comms y entregables (sombrero chico) | | |

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
Slack), persistir `llm_calls` (costo por corrida), secretos, la interfaz web
(talleres incluidos) y el coordinador que elige el agente de cada mensaje.

## 3. Agentes y orquestación

**Carpetas:** `src/onboarding/agents/`, `llm/factory.py`

**Tu agente:** el Diseñador de misiones (`agents/generate_quest/`): propone
misiones nuevas a partir de la documentación de un puesto.

**Primer PR:** el Diseñador de verdad, contra `knowledge.retrieve`, devolviendo
misiones con el formato de `data/quests.yaml`.

Después: las tools que usan todos los agentes (`agents/tools.py`), versionado de
prompts, y la comparación de dos modelos para justificar costo y latencia con datos.

## 4. RAG y evaluación

**Carpetas:** `src/onboarding/knowledge/rag/`, `eval/rag_questions.yaml`

Parte de la knowledge layer: **lo escrito**.

**Tu agente:** Conocimiento (`agents/answer_question/`): responde dudas citando
documento y sección y, si no hay respaldo, deriva con `who_knows_about`.

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

**Tu nodo:** la Red informal (`agents/extract_knowledge/`): corre al final de
todas las conversaciones y guarda quién sabe qué, sin responder al usuario.

**Primer PR:** tablas `nodes` y `edges` con su migración, y el esquema de
extracción (sujeto, relación, objeto, frase textual de respaldo).

Después: extracción estructurada desde las conversaciones, ground truth del grafo
hecho a mano, métrica de cobertura contra ese ground truth, y las consultas que
alimentan las próximas misiones.

## 6. Experiencia: interfaz y game design

**Carpetas:** `src/onboarding/game/`, `api/`, `bot/`

**Tu agente:** Mis misiones (`agents/quests/`): acompaña al ingresante en sus
misiones y le cuenta al jefe cómo viene su equipo, usando las funciones de `game/`.

**Primer PR:** tablas del juego y panel del jefe mostrando ingresantes y misiones
pendientes.

Después: `/misiones` en Slack, aprobación de un clic, las 6-8 misiones y el
catálogo de canje en `data/`, dial de tono, y la pantalla de transparencia que
le muestra al ingresante qué captura el agente.

## 7. Comms y entregables

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

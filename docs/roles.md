# Roles: quién hace qué y por dónde empezar

Los perfiles y sus tareas salen del documento de plataforma y roles del equipo.
Acá está la traducción a carpetas del repo y al primer PR de cada uno.

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

Después: repo en GitHub con `main` protegida y CODEOWNERS, proyecto en Neon,
servicio en Render, persistir `llm_calls` (costo por corrida), secretos.

## 3. Agentes y orquestación

**Carpetas:** `src/onboarding/agents/`, `llm/factory.py`

**Primer PR:** el nodo `answer_question` de verdad, contra `knowledge.retrieve`, con el
guardrail de "no sé, preguntale a X" cuando no hay soporte documental.

Después: los otros tres nodos, las tools, versionado de prompts, y la comparación
de dos modelos vía `LLM_MODEL` para justificar costo y latencia con datos.

## 4. RAG y evaluación

**Carpetas:** `src/onboarding/knowledge/rag/`, `eval/rag_questions.yaml`

Parte de la knowledge layer: **lo escrito**.

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

**Primer PR:** tablas `nodes` y `edges` con su migración, y el esquema de
extracción (sujeto, relación, objeto, frase textual de respaldo).

Después: extracción estructurada desde las conversaciones, ground truth del grafo
hecho a mano, métrica de cobertura contra ese ground truth, y las consultas que
alimentan las próximas misiones.

## 6. Experiencia: interfaz y game design

**Carpetas:** `src/onboarding/game/`, `api/`, `bot/`

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

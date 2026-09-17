# 0001 — Stack: Python, LangGraph, Postgres + pgvector, Slack

- Fecha: 2026-09
- Estado: aceptada
- Decide: el equipo, en base a la encuesta de stack (4 respuestas sobre 6)

## Contexto

Hay que elegir orquestador de agentes, lenguaje, base vectorial, interfaz y
deploy para un TP con 6 personas de experiencia dispar y tres meses de trabajo.
Dos señales de la encuesta pesan más que cualquier voto puntual: los cuatro que
respondieron marcaron los mismos tres intereses (orquestación multi-agente, RAG y
grafos de conocimiento) y **nadie** marcó infraestructura ni integraciones.
Además, alguien aclaró que prefiere arrancar por lo más sencillo para poder
empezar.

## Decisión

- Orquestación: **LangGraph** (única opción con mayoría; control fino del ciclo
  misión → validación → extracción). CrewAI queda como plan B.
- Lenguaje y backend: **Python + FastAPI** (unánime).
- RAG y base vectorial: **Postgres + pgvector**, una sola instancia para
  documentos, estado del juego y grafo.
- Interfaz: **bot de Slack** + panel web mínimo para el jefe.
- Grafo cultural: **tablas relacionales** de nodos y aristas.
- Deploy: contenedor Docker en un proveedor gestionado.
- Repositorio: **GitHub público, monorepo, PRs con review obligatorio**
  (requisito de la consigna).

## Consecuencias

- Stack chico: una base, un framework, un canal. Baja la barrera de entrada.
- El trabajo de infraestructura y evaluación, que nadie eligió, hay que
  asignarlo explícitamente: no lo va a levantar nadie solo.
- Neo4j, Redis, multi-tenant, SSO, multi-idioma y cualquier HRIS quedan fuera de
  alcance por decisión, no por olvido.

## Alternativas descartadas

CrewAI, Google ADK y OpenAI Agents SDK (menos votos); Chroma y Qdrant (otra base
más); Teams y WhatsApp (menos votos y peor de demostrar en vivo); Neo4j (el grafo
del TP entra en dos tablas).

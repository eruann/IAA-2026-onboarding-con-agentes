# 0009 — Un agente por rol, coordinador y talleres

- Fecha: 2026-11-01
- Estado: aceptada
- Decide: Tech Lead

## Contexto

Cada rol trabajaba sobre una pieza suelta (una función, una tabla) sin poder ver
el resultado ni cómo se conecta con el resto, y la documentación del repo casi
no se lee. En el diseño original el rol Agentes construía los cuatro nodos del
grafo y los demás roles solo le pasaban funciones: el que hacía la pieza no veía
el agente andando, y el que hacía el agente dependía de piezas sin terminar.

## Decisión

Cada rol construye **su agente** (un nodo del grafo de LangGraph) y lo prueba en
**su taller**. Un registro (`agents/registry.py`) lista los nodos y su dueño, y de
ahí se arma el grafo: coordinador → un agente → red informal (siempre al final,
sin responder). El coordinador es del Tech Lead; mientras no clasifique, respeta
el agente elegido y si no hay, va a Conocimiento. Todo turno entra por
`agents.run_turn`, que devuelve la respuesta y el recorrido por el grafo.

Cada rol declara su taller en un `workshop.py` de su carpeta: con qué agente
chatea y qué funciones propias prueba sueltas, salteando el agente. La interfaz
arma el formulario de cada prueba desde la firma de la función
(`onboarding/workshop.py`), así nadie necesita saber de interfaces para sumar
una prueba. Cada taller tiene un `LEEME.md` con lo que falta y pedidos listos
para Claude Code o Codex.

| Rol | Nodo |
|---|---|
| Tech Lead | `coordinator` |
| Agentes y orquestación | `generate_quest` (Diseñador de misiones) |
| RAG y evaluación | `answer_question` (Conocimiento) |
| Grafo cultural y datos | `extract_knowledge` (Red informal) |
| Experiencia | `quests` (Mis misiones) |

## Consecuencias

- Cada rol ve su agente funcionando desde el día uno (responde con su prompt) y
  completa lo que falta; el estado ✅/⏳ de cada dependencia se ve en la ficha.
- Un agente nuevo es una carpeta y una entrada en el registro: el grafo, el
  dibujo y el selector se actualizan solos.
- `agents/` ahora tiene carpetas de varios roles: cada uno toca solo la suya.
- La knowledge layer exporta `extract_triples` y los talleres de sus dos roles.
- Pendiente: el coordinador que clasifica y su set de evaluación; la interfaz
  web que muestra los talleres (PR siguiente).

## Alternativas descartadas

- Un laboratorio de pruebas aparte del chat: cada rol prueba sus cosas, no las
  de todos, así que se juntó en un taller por rol.
- Que el rol Agentes siga haciendo todos los nodos: es lo que dejaba a los demás
  sin ver resultados.
- Que la red informal también responda en el chat ("¿quién sabe de X?"): se
  pisaba con Conocimiento, que ya deriva con `who_knows_about`.

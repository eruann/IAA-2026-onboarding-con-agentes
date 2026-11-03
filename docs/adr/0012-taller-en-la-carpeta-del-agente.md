# 0012 — El taller de cada rol vive en la carpeta de su agente

- Fecha: 2026-11-03
- Estado: aceptada (reemplaza la parte de talleres de 0011)
- Decide: Tech Lead

## Contexto

Con [0011](0011-una-carpeta-por-agente.md) cada taller quedó en la carpeta del
rol, con una excepción: el de Grafo se mudó al lado de su agente, porque desde
`knowledge/` no podía importar las funciones del agente (`agents/` ya importa de
`knowledge/`). El resultado fue que dos carpetas de agente tenían taller y dos no,
que la carpeta de Grafo en `knowledge/` no tenía ni taller ni guía, y que las
pruebas salían de lugares distintos según el rol: quien pasaba de un rol a otro
no sabía dónde buscar. Además, los `__init__.py` de `game` y `knowledge`, que son
producto, exportaban talleres, que son andamiaje.

## Decisión

El taller vive en la carpeta del agente. Cada `agents/<nodo>/` tiene `node.py`,
`node_test.py`, `prompt.md`, `workshop.py`, `checks.py` (las pruebas ad hoc del
taller; está aunque no tenga ninguna) y `LEEME.md`. Lo que es producto o
compartido (knowledge layer, `game`) no se muda: el taller lo importa por su
interfaz pública. Los imports de cada `workshop.py` van en tres secciones fijas:
pruebas ad hoc (`checks.py`), del agente (`node.py`) y del código común. Una
carpeta de agente nunca importa de otra. Los talleres se encuentran por
convención (`workshop_modules`), sin que ningún módulo del producto los importe.
Tests controlan las tres secciones, los archivos de cada carpeta y los imports.

## Consecuencias

- Todas las carpetas de agente tienen la misma forma y todas las pruebas se
  buscan en el mismo lugar: el `workshop.py`, ordenado igual en todos. Cada
  tarjeta del taller muestra de qué sección sale la prueba.
- El producto ya no importa andamiaje: `game` y `knowledge` no exportan talleres.
- RAG y Experiencia tienen su guía en `agents/<su agente>/` y no en su carpeta de
  producto (`knowledge/rag/`, `game/`); el docstring de esos paquetes lo dice.
- Quien tenga una rama abierta que toque esos talleres tiene que actualizarla.
- Lo que comparten dos talleres no puede vivir en la carpeta de uno: va al
  producto común. La revisión de misiones que usan Experiencia y el Diseñador pasó
  a `game.review_rows`.

## Alternativas descartadas

- **El taller en la carpeta principal del rol:** el de Grafo tendría que importar
  del agente salteando la interfaz pública, y las carpetas de agente seguirían
  distintas.
- **Reexportar todo desde `checks.py`:** un solo lugar de donde salen las pruebas,
  pero esconde dónde vive cada función (`checks.extract_triples` está en
  `node.py`). Las tres secciones de `workshop.py` dan lo mismo sin ese paso.
- **Solo documentarlo:** sin un test, se desordena con el primer PR.

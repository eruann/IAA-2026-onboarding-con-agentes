# 0011 — Una carpeta por agente, prompts al lado del código y la misma estructura en cada rol

- Fecha: 2026-11-02
- Estado: aceptada
- Decide: Tech Lead

## Contexto

Cada rol construye su agente y su módulo. Con el tiempo cada uno quedó armado
distinto: dos agentes en un archivo común (`agents/nodes.py`) y dos en su propia
carpeta; todos los prompts juntos en `agents/prompts/`, lejos de su código (uno
lo usaba la knowledge layer); los talleres en tres lugares y exportados de tres
formas; las rutas a `data/` y `corpus/` calculadas en nueve lugares; la carga de
YAML y la sesión de base repetidas. Quien entendía un rol no podía leer los
demás de la misma forma.

## Decisión

Todos los roles tienen la misma estructura (detalle en `AGENTS.md`, "Cómo está
armado cada rol"):

- **Un agente, una carpeta:** `agents/<nodo>/` con `node.py` (`make_<nodo>` y su
  `NODE`: nombre, título, rol y prompt), `node_test.py` y `prompt.md`. Lo común,
  en `agents/common.py`. La lista de agentes está una sola vez, en `NODES`
  (`agents/graph.py`), y de ahí salen el grafo, el dibujo y el taller de Agentes.
- **El prompt va al lado del código que lo usa**, y `load_prompt` recibe su ruta.
  La llamada al modelo de un agente está en su carpeta, aunque use funciones de la
  knowledge layer: `extract_triples` vive en `agents/extract_knowledge/` y la capa
  guarda la forma de una relación (`KnowledgeTriple`) y las consultas.
- **Un taller que usa funciones de un agente se declara al lado del agente**
  (como el de Grafo y el del Diseñador): la knowledge layer no importa de `agents`.
- **Rutas y datos en `paths.py`**; la sesión propia, en `db.session.session_scope`.
- **El taller solo declara** (`workshop.py`); sus ayudas van en `checks.py`. Cada
  paquete los exporta en `WORKSHOPS` y el orden sale de `ROLE_ORDER`.
- **La lógica de producto vive en el producto:** las reglas de una misión, en
  `game/quests.py`; los tableros del Empleado y del Jefe, en `game/board.py`.
- **Lo pendiente** se marca igual en todos lados: `NotImplementedError` si la
  función todavía no hace lo que promete; `# TODO(<rol>)` si ya funciona y le
  falta algo.

## Consecuencias

- Leer un rol enseña a leer los demás, y copiar uno para empezar otro copia la
  forma correcta.
- Se movieron archivos de varios roles (RAG, Experiencia, Grafo, Diseñador; el
  taller y la guía de Grafo están ahora en `agents/extract_knowledge/`): quien
  tenga una rama abierta tiene que actualizarla con `main`.
- `ingest_directory` ahora avisa que está pendiente (corta, pero no guarda): el
  seed y su comando lo informan y siguen.

## Alternativas descartadas

- **Dejar que cada rol mueva su nodo cuando lo empiece:** así quedó a medias, y el
  que llega último copia la forma vieja.
- **Prompts todos juntos en una carpeta:** fáciles de encontrar, pero lejos del
  código que los usa, y uno terminaba siendo de otra capa.

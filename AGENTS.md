# Notas para agentes de código

Lo mínimo para trabajar en este repo sin romper los acuerdos del equipo.
Lo demás está en [CONTRIBUTING.md](CONTRIBUTING.md) y [docs/](docs/).

## Comandos

Todo corre en Docker. No instales Python en el host ni crees entornos virtuales
para correr la app o los tests (el `.venv` de `uv sync` en docs/setup.md es solo
para el panel Testing de VS Code, y lo arma la persona si quiere).

```bash
docker compose up --build                      # levantar
docker compose run --rm app pytest             # tests
docker compose run --rm app ruff check .       # lint
docker compose run --rm app ruff format .      # formato
docker compose run --rm app alembic upgrade head
docker compose run --rm app python -m onboarding.agents.lineage  # regenerar agents/grafo.json
```

`agents/grafo.json` es la arquitectura del grafo (nodos, flechas, qué usa cada
nodo de la knowledge layer y del modelo), generada desde el código. Si cambiás un
nodo, lo que llama o la interfaz de la knowledge layer, regeneralo y commitealo:
un test falla si está desactualizado, y su diff en el PR muestra qué cambió en la
arquitectura. Lo que cambia con el trabajo de cada rol (TODOs, funciones
pendientes, quién usa qué, chequeos de reglas) no va al JSON: la interfaz lo
calcula al abrir el panel.

El repo tiene un hook de pre-commit (`.githooks/pre-commit`) que corre Ruff sobre
los `.py` staged. Si un commit se frena por Ruff, corregí el error; no uses
`--no-verify` salvo pedido explícito.

## Reglas

1. **Antes de indicarle a alguien cómo configurar o integrar cualquier pieza
   del sistema (Slack, base de datos, deploy, el proveedor de modelo,
   autenticación, lo que sea), leé el código fuente real de esa integración
   — no solo los `.md`.** Los docs se desactualizan; el código no miente.
   Esto es especialmente crítico cuando hay una decisión de arquitectura tipo
   "modo A vs modo B" (Events API vs Socket Mode, sync vs async, polling vs
   webhook, etc.): el default "de manual" o el que más aparece en tutoriales
   puede no ser el que este repo implementó. La regla 12 (Slack) es un caso
   puntual de esta regla; no es la única integración donde puede pasar.
   Antes de dar la instrucción:
   - Ubicá el módulo real (`src/onboarding/...`) y confirmá con qué protocolo,
     variables de entorno y endpoints trabaja en la práctica (imports,
     inicialización de clientes, rutas registradas).
   - Si hay un ADR relacionado en `docs/adr/`, es la fuente de verdad sobre el
     *porqué*; el código es la fuente de verdad sobre el *qué* hay hoy. Ante
     cualquier diferencia entre lo que dice un `.md` y lo que hace el código,
     **gana el código**, y decilo explícitamente en tu respuesta (qué doc
     estaba desactualizado, qué dice el código).
   - Si la instrucción que ibas a dar no coincide con lo que ves en el
     código, no la dés: corregila primero y avisá la discrepancia, igual que
     si encontraras un bug.
2. **No commitees ni pushees** salvo pedido explícito.
3. Código, tablas y variables en inglés; comentarios, docs, prompts y UI en
   español rioplatense.
4. Los módulos se importan por su interfaz pública, nunca por sus archivos
   internos. A la knowledge layer se entra solo por `onboarding.knowledge`
   (`from onboarding.knowledge import retrieve`); `rag` e `informal_network` se
   usan directo únicamente desde adentro de la capa.
5. Todo modelo sale **siempre** de `onboarding.llm`; ningún módulo nombra un
   proveedor ni instancia un cliente. Cada tarea pide el modelo **por perfil**,
   según lo que necesita, nunca por nombre
   ([ADR 0014](docs/adr/0014-perfiles-de-modelo.md)):
   - **principal** (`get_chat_model()`, `LLM_MODEL`): conversar.
   - **estructurado** (`get_structured_model()`, `LLM_STRUCTURED_MODEL`): devolver
     datos con forma fija (salida estructurada). Vacío, usa el principal.
   - **embeddings** (`get_embeddings()`): textos a vectores. Uno solo para todo el
     sistema, porque solo se comparan vectores del mismo modelo; lo elige el
     ADR 0005.

   Un agente recibe los suyos en `Models` (`agents/common.py`) y usa `models.main`
   o `models.structured`. Un perfil nuevo se suma con un ADR, no por tarea.
6. Los prompts viven en un `.md` **al lado del código que los usa**, no
   embebidos en el código, y se cargan con `onboarding.llm.load_prompt(ruta)`.
   `prompt.md` es siempre el del agente (el que usa `ask_model`); si una función
   del agente necesita otras instrucciones, van al lado con su propio nombre
   (por ejemplo, `extraction_prompt.md` de `extract_triples`).
7. Función pública nueva, test nuevo. El test va al lado del módulo como
   `<modulo>_test.py` (pytest no reconoce otro nombre). Las fixtures están en
   `src/onboarding/conftest.py`. Los tests no llaman a modelos reales: está el
   proveedor `fake`.
8. Migraciones: una por cambio, con `downgrade()` que funcione. Las de datos,
   idempotentes.
9. Secretos jamás en el repo. Si hace falta una variable nueva, va a
   `config.py` y a `.env.example` (sin valor).
10. Si cambiás una decisión de arquitectura, escribí un ADR en `docs/adr/`.
11. Archivos compartidos (`config.py`, `db/models.py`, `knowledge/__init__.py`,
    `docker-compose.yml`, `pyproject.toml`): tocalos solo si la tarea lo pide, y
    decilo en el resumen.
12. **Slack usa Events API, no Socket Mode** ([ADR 0003](docs/adr/0003-slack-events-api.md)).
    El código (`src/onboarding/bot/`) solo sabe recibir `POST /slack/events` con
    `SLACK_BOT_TOKEN` + `SLACK_SIGNING_SECRET`; no usa `SLACK_APP_TOKEN` ni
    `SocketModeHandler`, y el manifest trae `socket_mode_enabled: false`.
    Ojo: `config.py` ignora variables desconocidas, así que un `SLACK_APP_TOKEN`
    en el `.env` no da error, simplemente no hace nada. Eventos, slash commands
    e interactividad van los tres a la misma URL `https://<host>/slack/events`.
    Si te piden ayudar a configurar Slack, la respuesta correcta es: en local,
    túnel público (`docker compose --profile tunnel up` o `--profile ngrok`);
    en producción, la URL de Render. Nunca Socket Mode. Pasos completos:
    [docs/setup.md](docs/setup.md#slack-solo-si-trabajás-en-el-bot) (local) y
    [docs/runbooks/deploy.md](docs/runbooks/deploy.md) (producción).
13. **Primero el plan.** Si alguien te pide cambiar código y no viene de un plan
    aprobado (no estás en modo plan y no hay un plan aceptado en la
    conversación), no edites todavía: contá en pocas líneas qué vas a hacer, qué
    archivos tocás y por qué, sugerile el modo plan (Claude Code: `Shift+Tab`;
    Codex: `/plan`) y esperá su OK. La idea es que quien pide entienda el
    cambio antes de que pase ([DEVELOPMENT.md](DEVELOPMENT.md#primero-el-plan)).

## Cómo está armado cada rol

Todos los roles tienen la misma estructura: si entendiste uno, podés leer los
demás.

```
src/onboarding/
  paths.py                 # raíz del repo, data/, corpus/, eval/ y load_data_yaml()
  db/session.py            # session_scope(): la sesión que te pasan o una propia
  agents/
    common.py              # Node, Models, ask_model y NodeSpec (lo compartido por los agentes)
    graph.py               # NODES (la lista de agentes) y el coordinador (route)
    workshop.py, checks.py, LEEME.md   # el taller del coordinador (rol Agentes)
    <nodo>/                # un agente: answer_question, validate_evidence, …
      node.py              # make_<nodo>(model) y su NODE (nombre, título, rol, prompt)
      node_test.py
      prompt.md            # su prompt, al lado del código
      workshop.py          # su taller: solo declara (andamiaje)
      checks.py            # las pruebas ad hoc del taller (+ checks_test.py si hay)
      LEEME.md             # la guía del rol: mismas secciones en todos
  knowledge/rag/, knowledge/informal_network/, game/   # producto de cada rol
    __init__.py            # su interfaz pública (lo único que importan los demás)
    <pieza>.py + <pieza>_test.py
```

- **Un agente nuevo:** su carpeta `agents/<nodo>/` con esos archivos (un test
  falla si falta alguno), su valor en `Intent` (`agents/state.py`) y su `NODE` en
  `NODES` (`agents/graph.py`). La llamada al modelo va en su carpeta, aunque use
  datos de la knowledge layer.
- **Una carpeta de agente nunca importa de otra carpeta de agente**, ni en los
  tests: solo de lo común (`agents/common.py`, `agents/state.py`,
  `onboarding.knowledge`, `onboarding.game`, `onboarding.llm`, `onboarding.paths`,
  `onboarding.workshop`). Un test lo controla.
- **El taller vive en la carpeta del agente** ([ADR 0012](docs/adr/0012-taller-en-la-carpeta-del-agente.md)).
  Lo que es producto o compartido (knowledge layer, `game`) no se muda: el
  `workshop.py` lo importa por su interfaz pública. Sus imports van en tres
  secciones, siempre iguales y en este orden (un test lo controla):
  `# 1. Pruebas ad hoc` (de su `checks.py`), `# 2. Del agente` (de su `node.py`) y
  `# 3. Del código común`. Una sección vacía lleva `# (ninguna)`. Cada tarjeta del
  taller muestra de cuál de las tres sale la prueba.
- **`checks.py` está siempre**, aunque no tenga pruebas ad hoc: son funciones
  armadas solo para probar o medir en el taller, que no son parte del producto.
  El producto nunca importa un `workshop.py` ni un `checks.py` (otro test).
- **Lo pendiente:** una función pública que todavía no hace lo que promete tira
  `NotImplementedError("TODO(<rol>): …")` (el taller y el grafo la muestran como
  pendiente). Algo que ya funciona pero le falta una parte lleva un comentario
  `# TODO(<rol>): …`.
- **Rutas y datos:** siempre desde `onboarding.paths` (nunca `Path("data")` ni
  `parents[3]`).

## Producto y andamiaje

Cada archivo de `src/` empieza con una marca y su leyenda (`file_tags_test.py`
falla si falta y muestra qué copiar):

```python
# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.
```

```python
# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.
```

En `.js` va con `//` y en los `LEEME.md` como cita (`>`). Buscar:
`grep -rl "^# andamiaje" src/`.

- **Producto:** el asistente en sí: `agents/` (grafo, nodos, estado, prompts),
  `knowledge/`, `llm/` (`factory.py`, `prompts.py` y `catalog.py`, la lista de
  modelos del selector), `game/`, `bot/`, `api/`, `db/`, `config.py`, `seed.py`, y
  de `ui/` la entrada, las pantallas de Empleado y Jefe y lo que usan
  (`entry.py`, `screens.py`, `chat.py`, `layout.py`, `errors.py`, `prefs.py`).
  Las migraciones (`db/migrations/versions/`) son producto y no llevan marca: las
  genera Alembic.
- **Andamiaje:** de `ui/`, los talleres (`pages.py`, `tool_form.py`,
  `access.py`, `grafo.js`), `onboarding/workshop.py`, cada
  `*/workshop.py`, `*/checks.py` y `LEEME.md`, `agents/lineage.py` y
  `agents/diagram.py`. Sin marca porque el formato no admite comentarios:
  `src/onboarding/agents/grafo.json` y, fuera de `src/`, `.tours/`.

**El producto funciona sin el andamiaje** ([ADR 0013](docs/adr/0013-producto-sin-andamiaje.md)):
borrarlo tiene que ser borrar sus archivos, sin tocar nada más.

- El producto (y sus tests) nunca importa un módulo de andamiaje. Al revés sí:
  el andamiaje importa lo que necesite, aunque no esté en la interfaz pública
  (por ejemplo, `ui/pages.py` importa `agents/diagram.py` directo).
- Si el andamiaje tiene que aparecer en una pantalla del producto, se engancha
  desde afuera: `ui/__init__.py` carga los talleres solo si están, y el botón
  "Talleres (Test)" lo suma `ui/pages.py` a `ENTRY_EXTRAS` de la entrada.
- Dos tests de `file_tags_test.py` (que sobrevive al borrado) lo controlan: uno
  busca imports del producto a andamiaje y el otro borra el andamiaje en una copia
  e importa todo lo que queda.

Archivo nuevo: elegí la marca según para qué sirve. Si es para el asistente, es
producto; si es para que el equipo trabaje o entienda, es andamiaje. Si una
parte de un archivo es de cada cosa, conviene separarlo en dos archivos.

## Talleres (interfaz `/ui/talleres`)

La interfaz (`/ui/`) arranca en una **entrada**: se elige una persona de la tabla
`people` y se va a la pantalla del Empleado o, con el tilde "Entrar como jefe", a
la del Jefe (producto, [ADR 0010](docs/adr/0010-entrada-por-persona.md)). Aparte,
el botón **Talleres (Test)**: directo en dev; en prod pide `ADMIN_PASSWORD`, y
sin ella los talleres quedan desactivados.


La interfaz web (`src/onboarding/ui/`, NiceGUI) tiene un **taller por rol**: un
chat con su agente y pruebas directas de sus funciones, con selector de modelo
([ADR 0009](docs/adr/0009-interfaz-nicegui-y-talleres.md)). Cada taller se
declara en el `workshop.py` de la carpeta de su agente (hoy: Agentes, RAG, Grafo,
Experiencia y Diseñador de misiones; la lista está en `docs/talleres.md`); su guía
es el `LEEME.md` de al lado. Una página de la app que el rol construye (como el panel del jefe) se
muestra dentro del taller con `embeds`.

**Guía completa para el equipo: [docs/talleres.md](docs/talleres.md)** (campos
del `Workshop`, tipos de parámetro y cómo se dibujan, cómo se muestra el
resultado, taller nuevo). Si alguien pregunta cómo armar o configurar su taller,
partí de esa guía y confirmalo en el código (`onboarding/workshop.py` y
`ui/tool_form.py`); si no coinciden, gana el código y corregí la guía en el
mismo PR. Si cambiás cómo funcionan los talleres, actualizá la guía.

Para sumar una prueba a un taller:

1. Escribí la función con tipo en **todos** los parámetros: en el producto si es
   parte del rol, o en el `checks.py` del agente si es una prueba ad hoc. Los tipos:
   `str`, `int`, `float`, `bool`, `Literal[...]`, `BaseChatModel | None` (se
   dibuja como selector de modelo, con opción de comparar dos) o `ChatHistory`
   (no se dibuja: recibe la conversación del chat del taller).
2. Importala en la sección que le toca del `workshop.py` y sumala a `tools` con
   `Tool(funcion, "Título", "Ayuda corta")`.
3. Test de la función al lado, como siempre. `workshop_test.py` falla si un
   parámetro no tiene tipo o es uno que la interfaz no sabe dibujar.

No hace falta tocar `ui/`: el formulario y la forma de mostrar el resultado
(texto, tabla o JSON) salen solos. Si la función todavía tira
`NotImplementedError`, el taller la muestra como pendiente con su archivo.

Los pedidos de ejemplo del `LEEME.md` de cada taller se escriben como pedidos de
plan ("Armame un plan para…, explicame…"), nunca como órdenes para copiar y
pegar ("Implementá…").

Un taller nuevo (otro rol): en la carpeta de su agente, `workshop.py` (solo la
declaración, con las tres secciones), `checks.py` y `LEEME.md`, y sumar el rol a
`ROLE_ORDER` en `onboarding/workshop.py`. La interfaz lo encuentra sola
(`workshop_modules`): no hay que exportarlo.

## Recorridos guiados (`.tours/`)

El equipo aprende el código con recorridos de CodeTour (`.tours/*.tour`). Las
preguntas que salen de ahí empiezan con `Recorrido <nombre>:`. Cuando veas una:

- Abrí `.tours/<nombre>.tour` y buscá el paso que contiene la pregunta: ahí
  están el archivo y el `pattern` de la línea de la que se habla. Leé ese código
  antes de responder.
- Quien pregunta no es dev. Respondé corto (un párrafo o una lista breve), sin
  jerga, y si usás un término técnico explicalo en media línea.
- Solo explicás: no modifiques archivos ni corras comandos que cambien algo,
  aunque la pregunta sea "¿cómo encararías...?".

Los comentarios `# recorrido: <nombre>` del código marcan dónde para cada paso.
**No los borres**: si movés esa parte del código, el marcador va con ella. Si
cambiás algo que un recorrido explica, fijate que el texto del paso siga siendo
cierto (con `grep -r "<nombre>" .tours/`). Es una guía para empezar, no
documentación completa: alcanza con que no mienta. Para crear o editar un
recorrido, seguí [.tours/README.md](.tours/README.md).

## Estado

Esqueleto: la mayoría de los módulos son stubs con `TODO(<rol>)`. Si te toca uno,
implementá ese módulo y sus tests, sin expandirte a las carpetas de otros roles.

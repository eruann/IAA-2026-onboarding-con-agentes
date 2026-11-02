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

`agents/grafo.json` es el lineage del grafo (nodos, qué usa cada uno, TODOs y
chequeos de reglas), generado desde el código. Si cambiás un nodo, lo que llama o
la interfaz de la knowledge layer, regeneralo y commitealo: un test falla si está
desactualizado, y su diff en el PR muestra qué cambió en la arquitectura.

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
5. El modelo se obtiene **siempre** de `onboarding.llm.get_chat_model()`. Ningún
   módulo nombra un proveedor ni instancia un cliente.
6. Los prompts viven en `src/onboarding/agents/prompts/*.md`, no embebidos en el
   código.
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

## Talleres (interfaz `/ui`)

La interfaz web (`src/onboarding/ui/`, NiceGUI) tiene un **taller por rol**: un
chat con su agente y pruebas directas de sus funciones, con selector de modelo
([ADR 0009](docs/adr/0009-interfaz-nicegui-y-talleres.md)). Cada taller se
declara en un `workshop.py` de la carpeta del rol (hoy:
`knowledge/informal_network/workshop.py`); su guía es el `LEEME.md` de al lado.

Para sumar una prueba a un taller:

1. Escribí la función en el módulo del rol, con tipo en **todos** los parámetros:
   `str`, `int`, `float`, `bool`, `Literal[...]` o `BaseChatModel | None` (este
   último se dibuja como selector de modelo, con opción de comparar dos).
2. Sumala a `tools` del `WORKSHOP` con `Tool(funcion, "Título", "Ayuda corta")`.
3. Test de la función al lado, como siempre. `workshop_test.py` falla si un
   parámetro no tiene tipo o es uno que la interfaz no sabe dibujar.

No hace falta tocar `ui/`: el formulario y la forma de mostrar el resultado
(texto, tabla o JSON) salen solos. Si la función todavía tira
`NotImplementedError`, el taller la muestra como pendiente con su archivo.

Los pedidos de ejemplo del `LEEME.md` de cada taller se escriben como pedidos de
plan ("Armame un plan para…, explicame…"), nunca como órdenes para copiar y
pegar ("Implementá…").

Un taller nuevo (otro rol): crear su `workshop.py` + `LEEME.md`, exportar
`WORKSHOP` por la interfaz pública del módulo y sumarlo en
`onboarding/workshop.py` (`all_workshops`).

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

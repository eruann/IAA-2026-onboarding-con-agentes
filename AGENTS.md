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
```

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

## Estado

Esqueleto: la mayoría de los módulos son stubs con `TODO(<rol>)`. Si te toca uno,
implementá ese módulo y sus tests, sin expandirte a las carpetas de otros roles.

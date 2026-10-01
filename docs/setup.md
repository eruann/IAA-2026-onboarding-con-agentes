# Puesta en marcha

## Lo único que se instala

| Sistema | Qué instalar |
|---|---|
| Linux | Docker Engine + plugin Compose, Git, VS Code |
| Windows | Docker Desktop (con backend WSL2), Git, VS Code |
| Mac | Docker Desktop, Git, VS Code |

Python **no** se instala: corre adentro del contenedor.

### Extensión de VS Code para ver los diagramas

La documentación usa diagramas Mermaid dentro de los `.md`
([docs/diagramas.md](diagramas.md)). La vista previa de VS Code no los dibuja
sin esta extensión:

**Markdown Preview Mermaid Support** (`bierner.markdown-mermaid`)

```bash
code --install-extension bierner.markdown-mermaid
```

También aparece sola: el repo la declara en `.vscode/extensions.json`, así que
VS Code ofrece instalarla la primera vez que abrís el proyecto.

Para ver un `.md` con sus diagramas: abrir el archivo y `Ctrl+Shift+V`
(`Cmd+Shift+V` en Mac), o `Ctrl+K V` para tenerlo al lado del texto.

En GitHub no hace falta nada: los diagramas se dibujan solos.

Opcional: [uv](https://docs.astral.sh/uv/) en el host, para correr los tests desde
el panel de VS Code y tener autocompletado. Ver [Tests desde VS Code](#tests-desde-vs-code).
No hace falta para trabajar.

## Arranque

```bash
git clone <url-del-repo>
cd IAA-2026-onboarding-con-agentes
cp .env.example .env          # Windows: copy .env.example .env
git config core.hooksPath .githooks
docker compose up --build
```

`git config core.hooksPath .githooks` activa el **hook de pre-commit** (una sola
vez por clon): antes de cada commit, Ruff formatea y corrige los `.py` que vas a
commitear, igual que Prettier. Corre dentro de Docker, así que tiene que estar
levantado; si no lo está, el hook avisa y deja pasar el commit (CI lo chequea
igual). Detalles en [CONTRIBUTING.md](../CONTRIBUTING.md#estilo).

Verificar: <http://localhost:8000/health> dice `ok` y
<http://localhost:8000/health/db> devuelve la versión de pgvector.

Cargar la empresa ficticia:

```bash
docker compose run --rm app python -m onboarding.seed
```

## Tests desde VS Code

Al abrir el proyecto, VS Code ofrece instalar las extensiones recomendadas:
**Python** (`ms-python.python`) y **Ruff** (`charliermarsh.ruff`), además de la
de diagramas. El repo ya trae la configuración compartida en `.vscode/`.

Hay dos formas de correr los tests desde el editor. Se pueden usar las dos.

### Opción A: panel Testing (como Jest/Vitest)

El ícono del matraz en la barra lateral lista todos los `*_test.py`, los corre
con un clic, muestra ✓/✗ al lado de cada test y permite debuggear con
breakpoints. Necesita un Python local **solo para el editor**; la app sigue
corriendo en Docker.

1. Instalar uv (una vez por máquina).

   Linux / Mac:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Windows (PowerShell):

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. En la carpeta del proyecto, crear el entorno (`.venv/`, ignorado por git).
   uv descarga Python 3.12 solo si no lo tenés:

   ```bash
   uv sync
   ```

3. En VS Code: `Ctrl+Shift+P` → **Python: Select Interpreter** → el de `.venv`.
   Suele elegirlo solo.
4. Abrir el panel **Testing**. Si no aparecen los tests, botón **Refresh Tests**.

Los tests con base (`@pytest.mark.db`) usan el Postgres del contenedor por el
puerto 5433: levantalo con `docker compose up -d db`. Si no está levantado, esos
tests aparecen salteados, no fallados.

Repetí `uv sync` cuando alguien agregue dependencias (cambia `uv.lock`).

### Opción B: tareas con Docker (sin instalar nada)

`Ctrl+Shift+P` → **Tasks: Run Task** y elegir:

| Tarea | Qué corre |
|---|---|
| **Tests (Docker)** | toda la suite, igual que CI. También con **Tasks: Run Test Task** |
| **Tests del archivo abierto (Docker)** | los tests del módulo que tenés abierto (filtra por nombre con `-k`) |
| **Formato y lint (Docker)** | `ruff check --fix` y `ruff format` sobre todo el repo |

La salida se ve en la terminal: no hay ✓/✗ por test ni debug con clic.

## Windows

- **Cloná dentro de WSL2** (`\\wsl$\Ubuntu\home\...`), no en `C:\Users\...`. En
  el sistema de archivos de Windows, Docker lee los archivos mucho más lento.
- El repo fuerza finales de línea LF (`.gitattributes`). No cambies esa
  configuración en tu Git: con CRLF se rompen cosas adentro del contenedor.
- El hot reload ya está resuelto (`WATCHFILES_FORCE_POLLING=true` en compose).
- Los comandos son idénticos en PowerShell y en bash. No hay scripts `.sh` ni
  `make`.

## Modelos

Por defecto `LLM_PROVIDER=fake`: respuestas fijas, sin red y sin costo. Alcanza
para levantar el proyecto y correr los tests.

Para usar un modelo real, en `.env`:

```
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
LLM_MODEL=anthropic/claude-haiku-4.5
```

Con una sola key se puede apuntar a cualquier modelo cambiando `LLM_MODEL`
(`openai/gpt-4o-mini`, `qwen/qwen-2.5-72b-instruct`, etc.).

### La key es de cada uno

**No hay una key compartida del equipo.** Cada uno usa la suya en su `.env`, que
está en `.gitignore` y nunca se sube. La key de la demo vive solo en las
variables de entorno de Render y la paga quien administra ese servicio: no se
comparte ni se usa para desarrollar.

Tres formas de trabajar sin gastar nada:

| Cómo | Para qué sirve |
|---|---|
| `LLM_PROVIDER=fake` (el default) | Levantar el proyecto, correr tests y trabajar en todo lo que no sea la respuesta del modelo |
| Modelos `:free` de OpenRouter | Probar el circuito real con tu propia cuenta, sin saldo (`meta-llama/...:free`, por ejemplo). Tienen límite de uso por día |
| Ollama local | Modelo abierto en tu máquina, sin cuenta ni internet. Pide RAM y anda más lento |

Ollama:

```bash
docker compose --profile local-llm up ollama
docker compose exec ollama ollama pull qwen2.5:7b
```

y en `.env`: `LLM_PROVIDER=openai_compat`, `LLM_MODEL=qwen2.5:7b`.

### Si el equipo cambia de proveedor

No estamos atados a OpenRouter ([ADR 0006](adr/0006-llm-via-openrouter.md)).
`openai_compat` sirve para **cualquier** proveedor con API compatible con OpenAI
(Groq, Together, DeepSeek, vLLM, Ollama): se cambian dos variables y listo.

```
LLM_PROVIDER=openai_compat
OPENAI_COMPAT_BASE_URL=https://api.del-proveedor.com/v1
OPENAI_COMPAT_API_KEY=...
LLM_MODEL=el-modelo-del-proveedor
```

Si el proveedor elegido no fuera compatible con OpenAI, el único archivo a tocar
es `src/onboarding/llm/factory.py`, y habría que escribir un ADR nuevo.

## Slack (solo si trabajás en el bot)

**El bot usa Events API, no Socket Mode** ([ADR 0003](adr/0003-slack-events-api.md)):
el código de `src/onboarding/bot/` solo expone `POST /slack/events` y valida
`SLACK_SIGNING_SECRET`, no acepta un `SLACK_APP_TOKEN` de Socket Mode. Por eso
los pasos de abajo arrancan con un túnel: no es una opción, es lo que el código
requiere. Si estás ayudando a alguien (persona o agente) a configurar Slack,
no sugieras Socket Mode como atajo para evitar el túnel — no va a andar.

Cada persona usa **su propia app de Slack de prueba**, en el workspace del
equipo: cada app manda los eventos a una sola URL, así que si dos comparten una,
los mensajes le llegan a uno solo. Pedí primero la invitación al workspace.

Se hace en dos tandas porque Slack **verifica la URL de eventos al activarla**,
y tu app local solo responde en `/slack/events` cuando ya tiene los tokens en el
`.env`.

1. Levantar la app con un **túnel**: Slack está en internet y tiene que poder
   mandarle eventos a tu máquina. El túnel te da una URL pública que redirige a
   tu `localhost:8000`. Hay dos opciones; las dos corren en Docker:

   | | Cloudflare Tunnel | ngrok |
   |---|---|---|
   | Cuenta | no hace falta | gratuita, una por persona |
   | URL | **cambia cada vez que reiniciás** | **fija**: se configura una vez en Slack |
   | Comando | `docker compose --profile tunnel up` | `docker compose --profile ngrok up` |

   Si vas a trabajar en el bot varios días, conviene **ngrok**: no tenés que
   actualizar la URL en la app de Slack cada vez que reiniciás.

   **Con Cloudflare:** la URL aparece en los logs del contenedor `tunnel`
   (`https://algo-random.trycloudflare.com`).

   **Con ngrok**, la primera vez:
   1. Crear cuenta en <https://dashboard.ngrok.com/signup>.
   2. Copiar tu **authtoken** en *Getting Started* → *Your Authtoken*.
   3. En *Domains*, tomar el dominio gratuito que te asigna (algo como
      `nombre-random.ngrok-free.app`).
   4. Cargar los dos en tu `.env` (son tuyos, no se comparten):

      ```
      NGROK_AUTHTOKEN=...
      NGROK_DOMAIN=nombre-random.ngrok-free.app
      ```

   Tu URL pública es `https://<NGROK_DOMAIN>`, siempre la misma.

2. Crear la app en <https://api.slack.com/apps> → **Create New App** → **From a
   manifest** → elegir el workspace del equipo. Pegar
   `src/onboarding/bot/manifest.yaml` con tres cambios:
   - reemplazar `TU-URL-PUBLICA` por la URL del túnel (aparece tres veces);
   - reemplazar `tu-nombre` por el tuyo (aparece dos veces), para no
     confundirla con las de los demás: `local-onboarding-matias`;
   - **borrar el bloque `event_subscriptions`** entero: se activa en el paso 5.

3. **Install App** → **Install to Workspace**, y copiar a tu `.env`:

   ```
   SLACK_BOT_TOKEN=xoxb-...          # Install App u OAuth & Permissions
   SLACK_SIGNING_SECRET=...          # Basic Information → App Credentials
   ```

4. Reiniciar la app para que lea el `.env`:

   ```bash
   docker compose up -d --force-recreate app
   ```

5. Activar los eventos: en la app de Slack → **Event Subscriptions** → **Enable
   Events** → Request URL `https://<tu-túnel>/slack/events` → tiene que decir
   **Verified**. En **Subscribe to bot events** agregar `app_mention` y
   `message.im` → **Save Changes** → reinstalar la app cuando lo pida.

6. Probar por **mensaje directo** con tu bot: en Slack, **Apps** (barra
   lateral) → `local-onboarding-tu-nombre` → pestaña **Messages** → escribile
   algo. Tiene que responder *"Te leo. Todavía no sé responder."*

   **Se prueba por DM, no en canales.** En el workspace del equipo hay una app
   de prueba por persona: un DM le llega solo a tu bot y a tu máquina, sin
   molestar a nadie ni mezclarse con las pruebas de los demás. En un canal
   compartido, además, el comando `/misiones` lo tienen registrado todas las
   apps, y Slack te hace elegir a cuál mandarlo.

   Si en la pestaña Messages dice que los mensajes están desactivados, en la
   app de Slack: **App Home** → *Show Tabs* → activar **Messages Tab** y
   **Allow users to send Slash commands and messages from the messages tab**.

Con Cloudflare, la URL del túnel **cambia cada vez que se reinicia**: hay que
actualizarla en tres lugares de la app de Slack (*Slash Commands*,
*Interactivity* y *Event Subscriptions*). Con ngrok no hace falta.

## Problemas frecuentes

| Síntoma | Qué pasa |
|---|---|
| `port is already allocated` | Tenés algo en el 8000 o en el 5433. Cambiá el puerto del host en `docker-compose.yml` |
| `/health/db` da 503 | La base todavía está arrancando, o falta `alembic upgrade head` |
| Los cambios en el código no se ven | Estás mirando un contenedor viejo: `docker compose up -d --build app` |
| Tests `db` salteados | No hay Postgres levantado. Corré los tests con `docker compose run --rm app pytest` |
| Commiteo y el código no se formatea (el hook no corre) | Los hooks no están activados en tu clon. Revisá con `git config --get core.hooksPath`: tiene que decir `.githooks`. Si no dice nada, activalos con `git config core.hooksPath .githooks` y volvé a commitear |
| El hook dice `Docker no está corriendo` pero Docker está levantado | Pasa con clientes gráficos de git (GitHub Desktop, Fork) que no encuentran `docker`. Commiteá desde la terminal o desde VS Code, o formateá a mano con `docker compose run --rm app ruff format .` |
| ngrok: `authentication failed: This ngrok session is not authenticated` | Falta `NGROK_AUTHTOKEN` en tu `.env`, o está mal copiado. Ver la sección Slack |
| El commit se frena con errores de Ruff | Ruff corrigió lo que pudo; lo que queda (por ejemplo un nombre indefinido) hay que arreglarlo a mano y volver a commitear |
| `pre-commit: estos archivos tienen cambios sin stagear` | El archivo tiene una parte en el commit y otra no. Hacé `git add` del archivo entero y volvé a commitear |
| Slack responde `dispatch_failed` | Tardaste más de 3 segundos: hay que hacer `ack()` primero y el trabajo pesado después |

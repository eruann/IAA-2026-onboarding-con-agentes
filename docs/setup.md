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
(`openai/gpt-4o-mini`, `qwen/qwen-2.5-72b-instruct`, etc.). Hay modelos `:free`
para desarrollo. Quién paga la key y con qué presupuesto lo define el equipo.

Modelo abierto local, sin gastar nada:

```bash
docker compose --profile local-llm up ollama
docker compose exec ollama ollama pull qwen2.5:7b
```

y en `.env`: `LLM_PROVIDER=openai_compat`, `LLM_MODEL=qwen2.5:7b`.

## Slack (solo si trabajás en el bot)

Cada persona usa **su propia app de Slack de prueba**: si dos comparten una, los
eventos van a una sola.

1. Levantar el túnel, que da una URL pública para tu entorno local:

   ```bash
   docker compose --profile tunnel up
   ```

   La URL aparece en los logs del contenedor `tunnel`
   (`https://algo-random.trycloudflare.com`).

2. Crear la app en <https://api.slack.com/apps> con **From an app manifest**,
   pegando `src/onboarding/bot/manifest.yaml` y reemplazando `TU-URL-PUBLICA`
   por la del paso 1 (aparece tres veces).

3. Instalar la app en el workspace y copiar a `.env`:

   ```
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_SIGNING_SECRET=...
   ```

4. Reiniciar: `docker compose up -d --force-recreate app`

La URL del túnel gratuito cambia cada vez que se reinicia: hay que actualizarla
en la configuración de la app de Slack.

## Problemas frecuentes

| Síntoma | Qué pasa |
|---|---|
| `port is already allocated` | Tenés algo en el 8000 o en el 5433. Cambiá el puerto del host en `docker-compose.yml` |
| `/health/db` da 503 | La base todavía está arrancando, o falta `alembic upgrade head` |
| Los cambios en el código no se ven | Estás mirando un contenedor viejo: `docker compose up -d --build app` |
| Tests `db` salteados | No hay Postgres levantado. Corré los tests con `docker compose run --rm app pytest` |
| Commiteo y el código no se formatea (el hook no corre) | Los hooks no están activados en tu clon. Revisá con `git config --get core.hooksPath`: tiene que decir `.githooks`. Si no dice nada, activalos con `git config core.hooksPath .githooks` y volvé a commitear |
| El hook dice `Docker no está corriendo` pero Docker está levantado | Pasa con clientes gráficos de git (GitHub Desktop, Fork) que no encuentran `docker`. Commiteá desde la terminal o desde VS Code, o formateá a mano con `docker compose run --rm app ruff format .` |
| El commit se frena con errores de Ruff | Ruff corrigió lo que pudo; lo que queda (por ejemplo un nombre indefinido) hay que arreglarlo a mano y volver a commitear |
| `pre-commit: estos archivos tienen cambios sin stagear` | El archivo tiene una parte en el commit y otra no. Hacé `git add` del archivo entero y volvé a commitear |
| Slack responde `dispatch_failed` | Tardaste más de 3 segundos: hay que hacer `ack()` primero y el trabajo pesado después |

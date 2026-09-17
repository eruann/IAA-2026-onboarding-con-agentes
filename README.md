# Onboarding gamificado con agentes de IA

Convierte el onboarding en un mapa de misiones operado por agentes: el ingresante
recibe misiones que lo obligan a recorrer procesos y personas reales, el agente
responde dudas con RAG sobre la documentación de la empresa citando la fuente, y
como subproducto se captura el conocimiento tácito de la organización (quién sabe
qué) en un grafo reutilizable.

Trabajo práctico de la cursada de IA, 2026.

## Arrancar (Linux, Mac o Windows)

Se instala **Git, Docker y VS Code** con la extensión
[Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid)
(`bierner.markdown-mermaid`, para ver los diagramas de `docs/`). Nada de Python
en la máquina.

```bash
git clone <url-del-repo>
cd IAA-2026-onboarding-con-agentes
```

Copiar la configuración de ejemplo — Linux/Mac:

```bash
cp .env.example .env
```

Windows (PowerShell):

```powershell
copy .env.example .env
```

Activar los hooks de git (una sola vez por clon, igual en Linux, Mac y Windows):

```bash
git config core.hooksPath .githooks
```

Con eso, cada commit formatea y corrige los `.py` con Ruff. **Si al commitear no
se formatea nada, casi siempre es porque este paso quedó sin hacer**: ver
[docs/setup.md](docs/setup.md#problemas-frecuentes).

Levantar todo:

```bash
docker compose up --build
```

Listo: <http://localhost:8000/health> responde `ok` y el panel del jefe está en
<http://localhost:8000/panel>. Sin tocar el `.env` el proyecto arranca con el
proveedor de modelo `fake`: no hace falta ninguna API key para empezar.

## Comandos

Los mismos en PowerShell y en bash.

| Para | Comando |
|---|---|
| Levantar todo | `docker compose up --build` |
| Apagar | `docker compose down` |
| Tests | `docker compose run --rm app pytest` |
| Lint | `docker compose run --rm app ruff check .` |
| Formatear | `docker compose run --rm app ruff format .` |
| Nueva migración | `docker compose run --rm app alembic revision --autogenerate -m "que hace"` |
| Aplicar migraciones | `docker compose run --rm app alembic upgrade head` |
| Cargar la empresa ficticia | `docker compose run --rm app python -m onboarding.seed` |
| Ingesta del corpus | `docker compose run --rm app python -m onboarding.knowledge.rag corpus` |
| Consola SQL | `docker compose exec db psql -U onboarding -d onboarding` |
| Slack con URL pública | `docker compose --profile tunnel up` |
| Borrar la base local | `docker compose down -v` |

Detalles de instalación, Windows/WSL2 y app de Slack: [docs/setup.md](docs/setup.md).

## Cómo está hecho

Un solo proceso sirve la API, el panel del jefe y el endpoint de Slack; al lado,
Postgres con pgvector guarda documentos, estado del juego y red informal.

El corazón es una **knowledge layer**: todo lo que la organización sabe, lo
escrito y lo no escrito (quién es quién más allá del organigrama). El sistema la
construye y, por ahora, la usa para el onboarding.

**Deploy**: la demo corre en [Render](https://render.com) (aplicación) +
[Neon](https://neon.tech) (Postgres con pgvector). Cada merge a `main` con CI en
verde se despliega solo. En desarrollo cada uno usa su base local de Docker, no
Neon. Detalle en [DEVELOPMENT.md](DEVELOPMENT.md#entornos-dónde-corre-cada-cosa).

```
src/onboarding/
├── config.py     variables de entorno, un solo lugar
├── seed.py       carga la empresa ficticia
├── db/           sesión y migraciones
├── llm/          elección de modelo (OpenRouter / fake / local) y costo
├── agents/       grafo de LangGraph, prompts y tools
├── knowledge/    knowledge layer: una sola puerta
│   ├── rag/              lo escrito: ingesta, búsqueda, citas
│   └── informal_network/ lo no escrito: quién es quién
├── game/         misiones, puntos, canje, tono
├── api/          rutas y panel web
└── bot/          Slack por Events API
```

Cada módulo tiene su test al lado: `chunking.py` + `chunking_test.py`.

- **Empezar a desarrollar** (roles, carpetas, forma de trabajo): [DEVELOPMENT.md](DEVELOPMENT.md)
- Arquitectura completa: [docs/arquitectura.md](docs/arquitectura.md)
- Quién hace qué y cuál es tu primer PR: [docs/roles.md](docs/roles.md)
- Cómo se trabaja (ramas, PRs, tests, migraciones): [CONTRIBUTING.md](CONTRIBUTING.md)
- Decisiones tomadas y por qué: [docs/adr/](docs/adr/)

## Alcance

Una empresa ficticia con documentación cargada por el equipo, 2-3 agentes y 6-8
misiones. Fuera de alcance por decisión: multi-tenant, SSO, integración con un
HRIS real, multi-idioma e integración real con plataformas de beneficios.

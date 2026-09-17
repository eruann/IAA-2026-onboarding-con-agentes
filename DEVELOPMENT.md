# Desarrollo

Punto de partida para trabajar en el proyecto. Si es tu primera vez, seguí este
orden:

1. **Levantá el proyecto**: [docs/setup.md](docs/setup.md).
2. **Entendé cómo está armado**: [docs/diagramas.md](docs/diagramas.md). Empezá
   por el diagrama 2 (módulos y dependencias) y el 3 (el grafo de LangGraph, el
   orquestador). Con esos dos se entiende dónde encaja tu parte.
3. **Buscá tu rol** en la tabla de abajo y mirá sus carpetas.
4. **Leé cómo se trabaja** (más abajo) antes de abrir tu primer PR.

## Roles y carpetas

Cada rol trabaja sobre todo en **sus carpetas**. La columna "También mirar" lista
lo que conviene conocer porque tu parte lo usa o lo alimenta, aunque no lo
modifiques. Todas las rutas de código son relativas a `src/onboarding/`, salvo
las que empiezan en la raíz del repo.

| Rol | Sus carpetas | También mirar |
|---|---|---|
| **PM / Producto** | `docs/`, `corpus/`, `data/`, `eval/baseline/` | `eval/rag_questions.yaml`, `data/quests.yaml` |
| **Tech Lead / Plataforma** | `config.py`, `db/`, `llm/callbacks.py`, `llm/models.py`, `conftest.py`; en la raíz: `Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `alembic.ini`, `render.yaml`, `.github/` | `api/main.py`, `docs/runbooks/` |
| **Agentes y orquestación** | `agents/` (incluye `agents/prompts/`), `llm/factory.py` | `knowledge/__init__.py` (la puerta de la knowledge layer), `game/` |
| **RAG y evaluación** · lo escrito | `knowledge/rag/`; en la raíz: `corpus/`, `eval/rag_questions.yaml` | `knowledge/__init__.py`, `docs/adr/0005-embeddings.md` |
| **Grafo cultural y datos** · lo no escrito | `knowledge/informal_network/`; en la raíz: `eval/informal_network_ground_truth.yaml` | `knowledge/__init__.py`, `agents/prompts/extract_knowledge.md`, `data/people.yaml` |
| **Experiencia: interfaz y game design** | `game/`, `api/`, `bot/`; en la raíz: `data/quests.yaml`, `data/rewards.yaml` | `agents/__init__.py`, `bot/manifest.yaml` |
| **Comms y entregables** | `docs/minutas/`, `docs/README.md` | `docs/adr/` |

El detalle de cada rol, con su primer PR, está en [docs/roles.md](docs/roles.md).

**Archivos compartidos**: `config.py`, `db/models.py`, `knowledge/__init__.py`,
`docker-compose.yml` y `pyproject.toml` los tocan varios roles. Avisá en el chat
antes de cambiarlos: ahí es donde aparecen los conflictos de merge.

## Cómo se trabaja

### El ciclo de una tarea

1. **Rama desde `main` actualizado**, con el formato `feat/area-tarea`,
   `fix/...`, `docs/...` o `chore/...` (ejemplo: `feat/rag-ingesta`).
2. **Código y test juntos**: cada `modulo.py` tiene su `modulo_test.py` al lado.
3. **Antes de abrir el PR**, correr lo mismo que corre CI:

   ```bash
   docker compose run --rm app ruff format .
   docker compose run --rm app ruff check .
   docker compose run --rm app pytest
   ```

4. **Pull Request** completando la plantilla. CI corre lint, tests,
   reversibilidad de migraciones y build.
5. **Review y merge**: el dueño del repo revisa y mergea con squash. Nadie
   pushea directo a `main`.
6. **Deploy**: automático. Render despliega `main` cuando CI está en verde.

Detalle de ramas, tests, migraciones y secretos: [CONTRIBUTING.md](CONTRIBUTING.md).

### Reglas que más se olvidan

- A la knowledge layer se entra solo por `onboarding.knowledge`.
- El modelo se obtiene siempre de `onboarding.llm.get_chat_model()`; los tests
  usan el proveedor `fake` y nunca gastan tokens.
- Los prompts van en `agents/prompts/*.md`, no dentro del código.
- Una migración por PR, con `downgrade()` que funcione.
- Una decisión de arquitectura nueva se escribe como ADR en
  [docs/adr/](docs/adr/).

### Trabajar con agentes de código

Este proyecto se desarrolla con agentes de código (Claude Code, Copilot, Cursor,
etc.). Todos leen [AGENTS.md](AGENTS.md) antes de tocar el repo (Claude Code, vía
`CLAUDE.md`). Lo que está ahí, el agente lo respeta; lo que no está, lo inventa.

**Cuando el equipo defina algo, escribilo en `AGENTS.md` en el mismo PR.** Por
ejemplo:

- una convención nueva ("las tools de los agentes devuelven siempre un dataclass");
- un comando que hay que correr ("después de tocar el corpus, reindexar");
- algo que no hay que hacer ("no llamar a `retrieve` desde `game`");
- un cambio en la estructura de carpetas o en las interfaces públicas.

Si una decisión queda solo en el chat o en la minuta, el próximo agente (y la
próxima persona) no la va a conocer.

Mantenelo corto: `AGENTS.md` son reglas y comandos. El porqué va en el ADR o en
[docs/arquitectura.md](docs/arquitectura.md), y `AGENTS.md` lo enlaza.

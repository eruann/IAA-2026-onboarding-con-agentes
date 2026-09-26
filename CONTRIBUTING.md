# Cómo se trabaja

## Ramas y PRs

- Nadie pushea a `main`. Todo entra por Pull Request.
- Rama: `feat/area-tarea`, `fix/...`, `docs/...`, `chore/...`
  (ejemplo: `feat/rag-ingesta`).
- **El dueño del repo revisa y mergea todos los PRs.** Los PRs que abre el dueño
  los aprueba otra persona (GitHub no deja aprobar el propio).
- Merge con squash: un commit por PR en `main`.
- PR chico y que funcione. Es mejor entregar la mitad andando que todo a medias.

## Quién toca qué

Cada uno trabaja dentro de las carpetas de su rol ([docs/roles.md](docs/roles.md)).

Los módulos se llaman entre sí **solo por su interfaz pública**:

```python
from onboarding.knowledge import retrieve  # sí: la puerta de la knowledge layer
from onboarding.knowledge.rag import retrieve  # no, desde fuera de la capa
from onboarding.knowledge.rag.retriever import _score  # nunca
```

Cinco archivos son de todos: `src/onboarding/config.py`,
`src/onboarding/db/models.py`, `src/onboarding/knowledge/__init__.py`,
`docker-compose.yml` y `pyproject.toml`. Ahí es
donde se generan los conflictos de merge: avisá en el chat antes de tocarlos.

## Estilo

- Código, nombres de tablas y variables en **inglés**; comentarios, documentos,
  prompts y textos de la UI en **español**.
- `ruff` decide el formato; no se discute. Lo aplica solo el **hook de
  pre-commit** (`.githooks/pre-commit`), que se activa una vez por clon con
  `git config core.hooksPath .githooks`. En cada commit:
  - los `.py` staged se corrigen (`ruff check --fix`), se formatean
    (`ruff format`) y se vuelven a agregar al commit;
  - si queda un error que Ruff no corrige solo, el commit se frena;
  - si un archivo tiene cambios staged y sin stagear a la vez, no se toca: el
    commit se frena si no está formateado, para no mezclar cambios;
  - si Docker no está corriendo, avisa y deja pasar. CI lo chequea igual.

  Saltearlo en un caso puntual: `git commit --no-verify`. A mano, sobre todo el
  repo: `docker compose run --rm app ruff format .` y
  `docker compose run --rm app ruff check --fix .`
- Comentarios: explican *por qué*, no *qué*. Los TODO van con el rol responsable:
  `# TODO(rag): ...`

## Tests

Los tests viven **al lado del código**, como en TypeScript. Cada módulo tiene su
test en la misma carpeta:

```
src/onboarding/knowledge/rag/
├── chunking.py
├── chunking_test.py
├── citations.py
└── citations_test.py
```

| TypeScript (Vitest/Jest) | Acá (pytest) |
|---|---|
| `chunking.test.ts` | `chunking_test.py` |
| `vitest` encuentra `*.test.ts` | `pytest` encuentra **solo** `*_test.py` |
| `describe` / `it` / `expect` | funciones `test_...` con `assert` |

Es `_test.py` y no `.test.py` porque en Python el punto rompe los imports. Un
archivo llamado `test_algo.py` **no** se ejecuta: hay una sola convención.

Los tests se suben al repo y CI los corre en cada PR, pero no entran en la imagen
Docker de producción (`.dockerignore`). CI verifica que así sea.

Quien agrega una función pública, agrega su test en el mismo PR.

Tres capas, separadas por marker:

| Capa | Marker | Toca | Cuándo corre |
|---|---|---|---|
| Unitaria | ninguno | funciones puras, sin base ni red | siempre |
| Integración | `@pytest.mark.db` | Postgres real | siempre (CI levanta la base) |
| Evaluación | `@pytest.mark.llm` | modelo real, gasta plata | **nunca en CI**, solo a mano |

CI corre `pytest -m "not llm"` con `LLM_PROVIDER=fake`: nunca gasta tokens.

Fixtures ya disponibles en `src/onboarding/conftest.py` (se usan desde cualquier
test sin importarlas): `db_session` (transacción que se
revierte sola al terminar el test), `client` (API), `fake_llm` (modelo con
respuestas fijas), `sample_corpus` (documentos de ejemplo).

Convenciones:

- Nombre: `test_<qué>_<caso>_<resultado esperado>`.
- Cuerpo en tres bloques: preparar, ejecutar, verificar.
- Nada de `datetime.now()` ni random sin control: se inyectan.
- **No se testea la salida de un modelo real**: no es determinística. Se testea
  el armado del prompt, el parseo de la respuesta y el guardrail de citas. La
  calidad del modelo se mide en `eval/`, que es otra cosa.
- La cobertura se reporta como dato, sin umbral que bloquee. Lo que bloquea es
  la regla de arriba: función pública nueva sin test, no se mergea.

## Migraciones

Una migración por PR. Si CI dice que hay dos cabezas, rebasá sobre `main` y
regenerá la tuya.

```bash
docker compose run --rm app alembic revision --autogenerate -m "agrega tabla chunks"
docker compose run --rm app alembic upgrade head
```

**Toda migración implementa `downgrade()`.** CI lo verifica corriendo
`upgrade head` → `downgrade base` → `upgrade head` en una base limpia: si no se
puede revertir, el PR no pasa. Si revertir es imposible, se explica por qué en el
docstring de la migración y se avisa en el PR.

Migraciones de datos (rellenar una columna, reescribir filas, mover datos):

1. Van en Alembic como las de esquema: un solo orden de versiones.
2. Son **idempotentes**: correrlas dos veces no duplica nada.
3. Si son destructivas, primero copian las filas afectadas a
   `<tabla>_backup_<revisión>` dentro de la misma migración, y el `downgrade`
   restaura desde ahí. Esa tabla se borra en una migración posterior, cuando ya
   se comprobó que todo anda.
4. Tienen test de ida y vuelta: insertar, aplicar, verificar, revertir,
   verificar que volvió al estado original.
5. **Expand/contract** para cambios que rompen: primero agregar y rellenar,
   después cambiar el código, y recién en otro PR borrar lo viejo. Nunca se
   borra en el mismo release que deja de usarlo, así un rollback no pierde datos.

Revertir en producción: [docs/runbooks/migraciones.md](docs/runbooks/migraciones.md).

## Decisiones

Las decisiones de arquitectura se escriben como ADR en `docs/adr/`, numeradas,
de una página, con fecha y motivo. No se editan una vez aceptadas: si la decisión
cambia, se escribe una nueva que marca la anterior como reemplazada.

## Secretos

Nunca en el repo. Van en `.env` local (ignorado por git) y en las variables de
entorno de Render. Si se filtra una key: rotarla primero, limpiar el historial
después.

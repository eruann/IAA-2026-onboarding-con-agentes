# 0008 — Migraciones al arrancar el contenedor, no como pre-deploy

- Fecha: 2026-09-26 (la decisión se aplicó en los PRs #5 y #6)
- Estado: aceptada. Reemplaza la parte de migraciones del [ADR 0004](0004-deploy-render-neon.md)
- Decide: dueño del repo + rol Plataforma

## Contexto

El ADR 0004 decía que Render corre `alembic upgrade head` como pre-deploy. Al
configurar el servicio apareció que `preDeployCommand` existe solo en los planes
pagos de Render, y la demo está en el plan gratuito. Tampoco sirve ponerlo como
`dockerCommand` en `render.yaml`: Render pasa las comillas literales y el
comando no se encuentra.

## Decisión

La etapa `prod` del `Dockerfile` arranca con
`alembic upgrade head && exec uvicorn ...`: cada contenedor nuevo migra la base
y, solo si eso sale bien, levanta la app. `render.yaml` no define comando de
arranque ni pre-deploy.

## Consecuencias

- Anda en el plan gratuito, sin pasos manuales en cada deploy.
- Si una migración falla, el contenedor nuevo no levanta y Render sigue sirviendo
  la versión anterior. La base queda como estaba: `db/migrations/env.py` corre
  todo el `upgrade` en una transacción y Postgres revierte también el DDL. La
  excepción son operaciones que no pueden ir en transacción (por ejemplo
  `CREATE INDEX CONCURRENTLY`).
- Los datos de Neon no se pisan en un deploy: `upgrade head` aplica solo las
  migraciones pendientes (las que no figuran en `alembic_version`), nunca
  recrea tablas, y ni el seed ni la ingesta corren solos. Lo que protege los
  datos son las reglas de migraciones de CONTRIBUTING.md (backup de filas,
  expand/contract) y la branch de Neon antes de una migración de datos
  ([runbooks/migraciones.md](../runbooks/migraciones.md)).
- **Supone una sola instancia.** Con dos o más, cada una migraría al arrancar y
  podrían pisarse. El plan gratuito corre una sola; si se escala o se pasa a un
  plan pago, hay que volver a `preDeployCommand` y escribir un ADR nuevo.
- Una migración lenta demora el arranque y puede hacer fallar el health check de
  Render (`/health`): las migraciones pesadas se hacen en pasos chicos.

## Alternativas descartadas

- `preDeployCommand` de Render: la opción limpia, pero solo en planes pagos.
- Correr las migraciones a mano antes de cada deploy: se olvida, y el deploy es
  automático al mergear a `main`.
- Migrar desde GitHub Actions contra Neon: obliga a guardar la URL de Neon como
  secreto también en GitHub, y la migración correría antes de saber si el build
  de Render sale bien.

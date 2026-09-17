# 0004 — Deploy en Render + Neon

- Fecha: 2026-09-15
- Estado: aceptada
- Decide: dueño del repo

## Contexto

Con Slack por Events API (ADR 0003), la demo necesita solo un servicio web Docker
y un Postgres con pgvector. El presupuesto del TP es chico y nadie del equipo
eligió infraestructura en la encuesta, así que el mantenimiento tiene que ser
cercano a cero.

## Decisión

- **Render**: Web Service construido desde el `Dockerfile` (etapa `prod`),
  configurado por `render.yaml` versionado. Despliega `main` después de que pasen
  los checks de CI y corre `alembic upgrade head` como pre-deploy.
- **Neon**: Postgres con la extensión `vector`, plan gratuito, persistente.

## Consecuencias

- Costo cero para empezar, sin tarjeta obligatoria para la base.
- La base no vence ni se borra sola, y sobrevive a cualquier cambio del servicio
  web.
- El plan gratuito de Render duerme tras ~15 minutos sin tráfico: el primer
  request después tarda. Con `ack()` inmediato y los reintentos de Slack es
  tolerable; si molesta, se paga el plan chico la semana de la demo.
- Infra en dos proveedores: dos cuentas y dos paneles.
- Neon permite crear branches de la base: red de seguridad antes de una
  migración de datos (ver el runbook).

## Alternativas descartadas

- **Todo en Render**: el Postgres gratuito se borra a los ~30 días, así que en la
  práctica hay que pagar la base desde el principio.
- **Railway**: sin cold start y todo en un proyecto, pero no tiene plan gratuito.
  Es el plan B si el cold start resulta insoportable.
- **VPS con Docker Compose**: control total y el mismo compose que corre local,
  pero alguien tiene que mantener servidor, TLS y backups; nadie eligió infra.

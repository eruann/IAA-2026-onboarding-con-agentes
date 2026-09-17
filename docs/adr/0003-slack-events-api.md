# 0003 — Slack por Events API en vez de Socket Mode

- Fecha: 2026-09-15
- Estado: aceptada
- Decide: dueño del repo + rol Experiencia

## Contexto

Bolt ofrece dos modos. **Socket Mode** abre un WebSocket saliente y no recibe
HTTP: no es un servicio web, así que necesita un proceso worker aparte del que
sirve la API y el panel. **Events API** recibe POST de Slack en una URL, que se
puede montar en la misma app FastAPI.

## Decisión

Events API. Un endpoint `POST /slack/events` dentro de la app, por donde entran
eventos, slash commands e interacciones con botones.

## Consecuencias

- Producción es **un solo contenedor**: más barato, un solo deploy, una sola
  configuración de variables.
- Events API es la forma más documentada de integrar Slack.
- En desarrollo hace falta una URL pública: perfil `tunnel` de compose con
  `cloudflared`. Solo lo necesita quien trabaja en el bot.
- Slack corta a los 3 segundos: los handlers tienen que hacer `ack()` inmediato y
  mandar el trabajo pesado (RAG + modelo) a un listener lazy. Es una restricción
  real de diseño, no un detalle.
- Hay que verificar la firma de cada request (`SLACK_SIGNING_SECRET`).

## Alternativas descartadas

Socket Mode: cómodo en desarrollo (no pide URL pública) pero obliga a un worker
en producción, que en los proveedores gestionados es un servicio más y, en varios
planes, uno más pago.

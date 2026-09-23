# Runbook: poner la demo online (Neon + Render + Slack)

Se hace una sola vez, en este orden: **Neon** (base) → **OpenRouter** (modelo) →
**Render** (aplicación) → **Slack** (bot). Cada paso necesita algo del anterior.

Titular: Tech Lead. Tiempo estimado: 30-45 minutos.

Decisión y motivos: [ADR 0004](../adr/0004-deploy-render-neon.md). La
infraestructura está versionada en [`render.yaml`](../../render.yaml).

---

## 1. Neon: la base de datos

<https://console.neon.tech>

1. Crear cuenta (se puede con la cuenta de GitHub) y un proyecto:
   - **Name**: `onboarding`
   - **Postgres version**: 16 o 17
   - **Region**: `AWS US West (Oregon)`. La app y la base tienen que estar en la
     **misma región**, para que cada consulta no cruce el país. La región de un
     proyecto de Neon **no se puede cambiar después**: si elegís otra, cambiá
     también `region` en [`render.yaml`](../../render.yaml) (valores válidos:
     `oregon`, `ohio`, `virginia`, `frankfurt`, `singapore`).
2. Habilitar pgvector. En **SQL Editor**, correr:

   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

   Verificar que quedó instalada:

   ```sql
   SELECT extversion FROM pg_extension WHERE extname = 'vector';
   ```

3. Copiar la connection string desde **Connect** / **Connection Details**. Neon
   da dos:
   - **directa**: `postgresql://usuario:clave@ep-algo.us-west-2.aws.neon.tech/neondb?sslmode=require`
   - **con pooler**: igual pero con `-pooler` en el host.

   **Usar la directa.** El pooler corre en modo transacción y rompe cosas que
   dependen de la sesión, como las migraciones. Guardala: es la `DATABASE_URL`
   del paso 3.

No hace falta convertir la URL: `config.py` le agrega el driver que necesita
SQLAlchemy (`postgresql+psycopg://`).

**Para qué sirve la base:** la usa solo producción. Nadie desarrolla contra Neon;
cada uno tiene su Postgres local en Docker.

## 2. OpenRouter: el modelo

<https://openrouter.ai/keys>

1. Crear cuenta y cargar saldo. Con USD 5 sobra para todo el TP: la propuesta
   estima USD 0,10-0,40 por ingresante simulado.
2. **Create Key**, nombre `onboarding-prod`. Copiar la key (`sk-or-...`): se
   muestra una sola vez.
3. **Ponerle un límite de crédito a la key** (*Credit limit* al crearla). Esta
   key la paga una sola persona y queda detrás de una URL pública: sin límite,
   un bucle en el código o alguien que encuentre la demo puede consumir el
   saldo. Con USD 2-3 de tope alcanza para la demo.

**Esta key es solo para producción.** Para desarrollar, cada uno usa la suya (o
`fake`, o un modelo local): ver [setup.md](../setup.md#la-key-es-de-cada-uno).

Con esa key funciona cualquier modelo cambiando `LLM_MODEL`; el default es
`anthropic/claude-haiku-4.5`. Ver [ADR 0006](../adr/0006-llm-via-openrouter.md).

## 3. Render: la aplicación

<https://dashboard.render.com>

1. Crear cuenta con GitHub y darle acceso al repositorio.
2. **New** → **Blueprint** → elegir el repo → Render lee `render.yaml` y propone
   el servicio `onboarding`, en la misma región que Neon (`oregon`).
3. Pide los valores marcados como secretos (`sync: false`). Cargar:

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | la connection string **directa** de Neon (paso 1) |
   | `OPENROUTER_API_KEY` | la key `sk-or-...` (paso 2) |
   | `SLACK_BOT_TOKEN` | dejar vacío por ahora; se completa en el paso 4 |
   | `SLACK_SIGNING_SECRET` | dejar vacío por ahora |

4. **Apply**. El primer build tarda unos minutos: construye la imagen Docker,
   corre `alembic upgrade head` y arranca la aplicación.
5. Anotar la URL que asigna Render: `https://onboarding-XXXX.onrender.com`.

**Verificar:**

- `https://<tu-url>/health` → `{"status":"ok"}`
- `https://<tu-url>/health/db` → `{"status":"ok","pgvector":"0.8.x"}`
- `https://<tu-url>/panel` → el panel del jefe, vacío

Si `/health/db` da 503, el problema está en la `DATABASE_URL` o en que falta
`CREATE EXTENSION vector`. Los logs están en **Logs**, en el panel del servicio.

**Cargar la empresa ficticia en producción** (cuando exista el corpus): en
**Shell**, dentro del servicio:

```bash
python -m onboarding.seed
```

## 4. Slack: el bot

<https://api.slack.com/apps>

Esta es la app **de producción**. Cada integrante que trabaje en el bot tiene
además su propia app de prueba, con un túnel local ([setup.md](../setup.md)).

1. **Create New App** → **From an app manifest** → elegir el workspace.
2. Pegar el contenido de [`src/onboarding/bot/manifest.yaml`](../../src/onboarding/bot/manifest.yaml),
   reemplazando `TU-URL-PUBLICA` por el dominio de Render (aparece tres veces) y
   cambiando el nombre a algo sin `dev`:

   ```yaml
   display_information:
     name: Onboarding
   features:
     bot_user:
       display_name: onboarding
   ```

   Las tres URLs quedan así: `https://<tu-url>.onrender.com/slack/events`
3. **Install to Workspace** y aceptar los permisos.
4. Copiar dos valores:
   - **Bot User OAuth Token** (`xoxb-...`), en *OAuth & Permissions*
   - **Signing Secret**, en *Basic Information*
5. Cargarlos en Render: servicio → **Environment** → editar `SLACK_BOT_TOKEN` y
   `SLACK_SIGNING_SECRET` → **Save**. Render redeploya solo.
6. Volver a Slack y verificar la Request URL: en *Event Subscriptions* tiene que
   decir **Verified**. Si dice que falló, esperar a que termine el deploy y
   tocar **Retry**.

**Verificar:** invitar al bot a un canal (`/invite @onboarding`) y escribir
`/misiones`. Tiene que responder el texto de ejemplo.

> **Cuidado con el plan gratuito de Render:** el servicio se duerme tras ~15
> minutos sin tráfico y tarda ~1 minuto en despertar. Slack corta a los 3
> segundos, así que **el primer mensaje después de un rato puede fallar**; el
> segundo anda. Para la demo, entrar a la URL unos minutos antes para
> despertarlo, o pagar el plan chico esa semana.

## 5. Cómo queda el circuito con CI

```
PR → CI (lint · tests · migraciones · build) → review → squash merge a main
                                                            ↓
                           Render espera a que los checks de main estén en verde
                                                            ↓
                    build de la imagen → alembic upgrade head → app nueva online
```

`autoDeployTrigger: checksPass` en `render.yaml` es lo que hace que Render
**espere al CI**: si los checks fallan, no despliega. No hace falta ningún
secreto de Render en GitHub: la integración va por la app de GitHub de Render.

Las migraciones corren **al arrancar el contenedor**, no como pre-deploy, porque
`preDeployCommand` existe solo en los planes pagos. Consecuencia: si una
migración falla, el contenedor nuevo no levanta y Render mantiene el anterior.

## Límites del plan gratuito

| Límite | Detalle |
|---|---|
| Render: spin down | ~15 minutos sin tráfico; ~1 minuto para despertar |
| Render: horas | 750 horas de instancia gratis por mes, por workspace |
| Render: una instancia | sin escalado horizontal (nos alcanza) |
| Neon: sin vencimiento | a diferencia del Postgres gratis de Render, que se borra a los 30 días |

## Si algo se rompe

| Síntoma | Qué mirar |
|---|---|
| El deploy no arranca solo | En Render: Settings → Auto-Deploy → **After CI Checks Pass**. Revisar también que los checks de `main` estén en verde |
| El deploy falla en el arranque | Logs de Render: suele ser una migración. Ver [migraciones.md](migraciones.md) |
| `/health` ok pero `/health/db` 503 | `DATABASE_URL` mal, o falta `CREATE EXTENSION vector` en Neon |
| Slack dice `dispatch_failed` | El servicio estaba dormido o el handler tardó más de 3 segundos |
| Slack no verifica la URL | El deploy no terminó, o `SLACK_SIGNING_SECRET` está mal cargado |
| Respuestas del agente con error de modelo | Saldo de OpenRouter agotado, o `LLM_MODEL` mal escrito |

Antes de una migración de datos en producción, crear una branch en Neon: ver
[migraciones.md](migraciones.md).

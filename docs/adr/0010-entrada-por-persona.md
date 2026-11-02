# 0010 — Entrada por persona, pantallas de Empleado y Jefe, talleres aparte

- Fecha: 2026-11-02
- Estado: aceptada
- Decide: Tech Lead

## Contexto

La interfaz (`/ui`, [ADR 0009](0009-interfaz-nicegui-y-talleres.md)) arrancaba
pidiendo un nombre cualquiera y llevaba a los talleres del equipo. Faltaban las
pantallas de quien usa el asistente (el ingresante y su jefe), que hasta ahora
solo se pensaban para Slack, y los talleres quedaban abiertos en la demo.

## Decisión

`/ui/` es una **entrada**: se elige una persona de la tabla `people` y se va a la
pantalla del **Empleado** (`/ui/empleado`) o, con el tilde "Entrar como jefe", a
la del **Jefe** (`/ui/jefe`). Las dos tienen el chat con el coordinador y un
tablero propio (el Jefe, el panel de `/panel`). Son producto.

Los **talleres** pasan a `/ui/talleres`, con un botón aparte en la entrada: en
dev se entra directo; en prod, solo con `ADMIN_PASSWORD`, y sin ella quedan
desactivados.

## Consecuencias

- Se puede mostrar el asistente como lo usaría la empresa, sin Slack.
- Los talleres son opcionales en la demo: nadie gasta modelo sin la clave.
- El tilde de jefe es provisorio: no hay dato de quién es jefe de quién. Queda
  como tarea de Experiencia con PM (`TODO(experiencia)` en `game/people.py`).
- La sesión sigue en el navegador (`localStorage`): elegir una persona no es
  autenticarse. Alcanza para una demo con una empresa ficticia, no para datos
  reales.

## Alternativas descartadas

- **Deducir quién es jefe por el puesto** ("Jefe…", "Jefa…"): frágil y deja
  afuera a referentes con gente a cargo.
- **Sesiones en el servidor** (`storage_secret` de NiceGUI): más configuración
  para una demo; la clave de los talleres se verifica con una huella guardada en
  el navegador.

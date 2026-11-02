# Taller Experiencia: el juego

**Tu agente:** Mis misiones (`agents/quests/node.py`). Acompaña al ingresante:
qué le falta, recibir y validar evidencia, puntos. Al jefe le cuenta cómo viene
su equipo.

**Tus carpetas:** `game/` (reglas y funciones del juego), `api/` (panel del
jefe, en HTMX) y las misiones en `data/quests.yaml` (con PM).

## Qué falta

1. Funciones de `game/` que usa tu agente: misiones de una persona, entregar
   evidencia, aprobar (`approve_assignment`, registrando quién y cuándo),
   puntos de una persona.
2. Botón "Aprobar" en el panel del jefe, que use esas mismas funciones.
3. El agente Mis misiones usando esas funciones como tools.

## Cómo probar

- **Nivel según puntos** y cada función de `game/` que sumes a tu taller.
- **El chat** de este taller le habla a tu agente.

## Pedidos listos para Claude Code o Codex

- `Agregá a game/ una función que devuelva las misiones de una persona por su key, con test db, y sumala a mi taller (game/workshop.py).`
- `Implementá approve_assignment en game/ registrando quién aprobó y cuándo, con test db.`
- `Agregá el botón Aprobar al panel (api/routes/panel.py) usando approve_assignment, con HTMX.`

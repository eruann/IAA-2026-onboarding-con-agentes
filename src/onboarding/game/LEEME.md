> **andamiaje**
>
> Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
> construya, pruebe o entienda el producto (talleres, diagramas, guías).
> No es parte del producto.

# Taller Experiencia

**Tu parte:** cómo vive el onboarding el ingresante y su jefe. Misiones, puntos,
canje, el panel del jefe y el bot de Slack.

## Qué construís y qué trae el taller

**Lo construís vos** (`game/`, `api/`, `bot/` y los datos en `data/`):

- `game/models.py`: tablas del juego. **Ya están.**
- `game/points.py` → `level_for`: el nivel según los puntos. **Ya funciona.**
- `api/routes/panel.py` y `api/templates/panel/`: el panel del jefe, con
  ingresantes y misiones pendientes. **Ya funciona.**
- `game/quests.py`: la forma de una misión (`Quest`), sus estados y sus reglas
  (`check_quests`). **Ya funciona.** El seed avisa si una misión no cumple las
  reglas.
- `game/board.py`: los tableros del Empleado (`employee_board`) y del Jefe
  (`manager_board`). **Ya funcionan**, solo leen.
- `game/data.py` → `sync_game_data`: carga personas y misiones de `data/` en la
  base (lo usa el seed). **Ya funciona.**
- `game/rewards.py`: catálogo, canje (descuenta puntos) e historial. Pendiente:
  las funciones ya están con su firma (`list_rewards`, `redeem`,
  `redemption_history`) y el taller las muestra como pendientes.
- `game/tone.py`: el dial de tono existe como opción; falta que cambie los textos.
- `bot/`: `/misiones` en Slack y la aprobación de un clic. Pendiente.
- `data/quests.yaml` y `data/rewards.yaml`, junto con PM.

**Lo trae el taller** (`game/workshop.py`, con las revisiones en `checks.py`): la declaración de las pruebas, el
panel del jefe adentro del taller y dos revisiones de los datos del juego:

- `review_quests`: muestra las misiones y marca lo que no cierra.
- `review_rewards`: muestra el catálogo y cuánto cuesta cada premio comparado
  con los puntos de todas las misiones.

No hace falta tocarlas para avanzar. Si cambiás qué campos tiene una misión o un
premio, ajustalas (tienen su test en `checks_test.py`).

## Qué falta

1. Las 6 a 8 misiones del TP en `data/quests.yaml` (hoy hay 4), con PM.
2. Cargar las misiones desde el YAML (`game/quests.py`).
3. Canje: catálogo, canjear e historial (`game/rewards.py`).
4. Aprobar o rechazar una misión desde el panel, con un clic.
5. `/misiones` en Slack.
6. El dial de tono y la pantalla de transparencia (qué captura el agente).
7. Desde la pantalla del Empleado (`/ui/empleado`, tablero en `game/board.py`):
   entregar la evidencia de una misión, canjear puntos y el dial de tono. Hoy el
   tablero solo muestra misiones, puntos y nivel.
8. Quién es jefe de quién: hoy la entrada de `/ui` deja tildar "Entrar como jefe"
   (ver el `TODO(experiencia)` de `game/people.py`). Con PM, sumar el jefe de cada
   persona a `data/people.yaml` y su columna en `people`, para que la entrada lo
   sepa sola y el panel muestre solo su equipo.

## Qué probar en el taller

- **Panel del jefe**: es tu pantalla, adentro del taller. Después de cambiar el
  panel, tocá **Recargar**. Muestra los datos de tu base: si está vacío, cargá
  la empresa ficticia con
  `docker compose run --rm app python -m onboarding.seed`.
- **Revisar las misiones**: cada vez que cambies `data/quests.yaml`. Marca si
  faltan misiones para llegar a 6-8, campos vacíos, `key` repetidas, puntos que
  no son un número positivo o un `approver` que no existe.
- **Ver el catálogo** y **Ver lo que canjeó una persona**: aparecen como
  pendientes hasta que las implementes. Canjear escribe en la base, así que no
  está como prueba del taller: se prueba desde la pantalla del Empleado.
- **Revisar el catálogo de canje**: para ajustar el balance con PM. Si un premio
  cuesta más que todas las misiones juntas, nadie lo puede canjear.
- **Calcular el nivel**: probá los bordes (99, 100, 250, 500).
- **Chat**: el agente que revisa evidencias (`validate_evidence`). Escribile
  como si entregaras la evidencia de una misión.

Para probar el bot de Slack en tu compu: [docs/setup.md](../../../docs/setup.md#slack-solo-si-trabajás-en-el-bot).

## Pedidos de plan para Claude Code o Codex

Prendé el modo plan (Claude Code: `Shift+Tab` hasta *plan mode*; Codex:
`/plan`; más detalle en `DEVELOPMENT.md`, "Primero el plan") y pedí, por
ejemplo:

- `Armame un plan para cargar las misiones de data/quests.yaml como Quest en game/quests.py. ¿Dónde se usa después?`
- `Armame un plan para aprobar una misión desde el panel del jefe con un clic, con HTMX. ¿Qué tabla cambia?`
- `Armame un plan para el canje en game/rewards.py: listar, canjear e historial. ¿Cómo evito canjear sin puntos suficientes?`
- `Armame un plan para /misiones en Slack. ¿Qué tengo que configurar para probarlo en mi compu?`

Leé el plan, preguntá lo que no entiendas y recién ahí aprobalo.

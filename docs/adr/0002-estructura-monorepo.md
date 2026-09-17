# 0002 — Monorepo con un paquete por área y una sola imagen Docker

- Fecha: 2026-09-15
- Estado: aceptada
- Decide: Tech Lead

## Contexto

Seis personas con roles distintos trabajando en paralelo sobre un sistema chico y
acoplado. Hace falta que cada uno sepa dónde escribe, que los conflictos de merge
sean raros y que el entorno sea idéntico en Linux y en Windows.

## Decisión

Un paquete Python (`src/onboarding/`) con un módulo por área: `agents`,
`knowledge` (con `rag` e `informal_network` adentro, ver ADR 0007), `game`, `api`,
`bot`, más `db`, `llm` y `config` como base común.
Cada módulo es dueño de sus tablas y expone su interfaz pública en `__init__.py`.

Los tests viven al lado del código que prueban (`chunking.py` +
`chunking_test.py`), como en TypeScript. pytest solo reconoce `*_test.py`. Se
versionan en el repo y corren en CI, pero `.dockerignore` los deja fuera de
todas las imágenes.

Una sola imagen Docker con etapas `dev` y `prod`: la API, el panel, Slack, las
migraciones, el seed y la ingesta son comandos distintos de la misma imagen.

Los comandos del día a día son `docker compose ...`, iguales en PowerShell y en
bash. No hay `Makefile` ni scripts `.sh` en el host.

Código, tablas y variables en inglés; comentarios, documentos, prompts y UI en
español.

## Consecuencias

- Cada rol tiene **una** carpeta propia, tests incluidos: los merges se vuelven
  simples y se ve a simple vista qué módulo no tiene test.
- Los tests no llegan a producción; CI falla si alguno se cuela en la imagen.
- Solo cuatro archivos son compartidos (`config.py`, `db/models.py`,
  `docker-compose.yml`, `pyproject.toml`); ahí se avisa antes de tocar.
- Una imagen para todo: menos build, menos deploy, menos divergencia entre
  desarrollo y producción.
- Un módulo que quiera escalar aparte más adelante hay que extraerlo; con el
  tamaño del TP no compensa preverlo hoy.

## Alternativas descartadas

- Repos separados por servicio: seis personas, tres meses, servicios acoplados.
- Carpeta `tests/` aparte, espejo de `src/`: es la convención clásica de pytest,
  pero le da a cada rol dos carpetas en vez de una.
- `Makefile`: no existe en Windows y era solo un alias de `docker compose`.
- Dev Container de VS Code: agrega una herramienta más que explicar, y el equipo
  pidió arrancar por lo más sencillo.

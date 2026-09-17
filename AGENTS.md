# Notas para agentes de código

Lo mínimo para trabajar en este repo sin romper los acuerdos del equipo.
Lo demás está en [CONTRIBUTING.md](CONTRIBUTING.md) y [docs/](docs/).

## Comandos

Todo corre en Docker. No instales Python en el host ni crees entornos virtuales.

```bash
docker compose up --build                      # levantar
docker compose run --rm app pytest             # tests
docker compose run --rm app ruff check .       # lint
docker compose run --rm app ruff format .      # formato
docker compose run --rm app alembic upgrade head
```

El repo tiene un hook de pre-commit (`.githooks/pre-commit`) que corre Ruff sobre
los `.py` staged. Si un commit se frena por Ruff, corregí el error; no uses
`--no-verify` salvo pedido explícito.

## Reglas

1. **No commitees ni pushees** salvo pedido explícito.
2. Código, tablas y variables en inglés; comentarios, docs, prompts y UI en
   español rioplatense.
3. Los módulos se importan por su interfaz pública, nunca por sus archivos
   internos. A la knowledge layer se entra solo por `onboarding.knowledge`
   (`from onboarding.knowledge import retrieve`); `rag` e `informal_network` se
   usan directo únicamente desde adentro de la capa.
4. El modelo se obtiene **siempre** de `onboarding.llm.get_chat_model()`. Ningún
   módulo nombra un proveedor ni instancia un cliente.
5. Los prompts viven en `src/onboarding/agents/prompts/*.md`, no embebidos en el
   código.
6. Función pública nueva, test nuevo. El test va al lado del módulo como
   `<modulo>_test.py` (pytest no reconoce otro nombre). Las fixtures están en
   `src/onboarding/conftest.py`. Los tests no llaman a modelos reales: está el
   proveedor `fake`.
7. Migraciones: una por cambio, con `downgrade()` que funcione. Las de datos,
   idempotentes.
8. Secretos jamás en el repo. Si hace falta una variable nueva, va a
   `config.py` y a `.env.example` (sin valor).
9. Si cambiás una decisión de arquitectura, escribí un ADR en `docs/adr/`.
10. Archivos compartidos (`config.py`, `db/models.py`, `docker-compose.yml`,
    `pyproject.toml`): tocalos solo si la tarea lo pide, y decilo en el resumen.

## Estado

Esqueleto: la mayoría de los módulos son stubs con `TODO(<rol>)`. Si te toca uno,
implementá ese módulo y sus tests, sin expandirte a las carpetas de otros roles.

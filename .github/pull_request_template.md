## Qué hace

<!-- Una o dos líneas. Si hay un acuerdo de la minuta detrás, linkealo. -->

## Cómo lo pruebo

<!-- Comando exacto que corrió quien revisa, o pasos en la UI. -->

## Checklist

- [ ] Toca solo carpetas de mi área (si toca `config.py`, `db/models.py`,
      `docker-compose.yml` o `pyproject.toml`, lo avisé en el chat)
- [ ] Las funciones públicas nuevas tienen su `<modulo>_test.py` al lado
- [ ] Si agrega tablas o cambia datos: una sola migración, con `downgrade()` que
      funciona y es idempotente
- [ ] Si cambia una decisión de arquitectura: hay un ADR nuevo en `docs/adr/`
- [ ] Si define una convención, un comando o una regla nueva: está en `AGENTS.md`
- [ ] No hay secretos ni datos reales en el diff

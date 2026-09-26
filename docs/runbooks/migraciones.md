# Runbook: migraciones

## Día a día

```bash
# crear
docker compose run --rm app alembic revision --autogenerate -m "que hace"
# aplicar
docker compose run --rm app alembic upgrade head
# probar que se puede revertir (esto mismo hace CI)
docker compose run --rm app alembic downgrade -1
docker compose run --rm app alembic upgrade head
```

Antes de abrir el PR, revisá el archivo generado: el autogenerate acierta con las
tablas, pero no sabe nada de datos ni de índices que quieras a mano.

## Dos cabezas

Síntoma: CI falla con "Hay 2 cabezas de Alembic". Pasa cuando dos personas crearon
una migración en paralelo.

```bash
git fetch origin && git rebase origin/main
# borrar tu archivo de migración y regenerarlo sobre la cabeza nueva
docker compose run --rm app alembic revision --autogenerate -m "que hace"
```

Preferí regenerar antes que `alembic merge`: el merge deja un historial que
después nadie entiende.

## Migración de datos, no de esquema

Reglas (también en CONTRIBUTING.md):

1. Idempotente: correrla dos veces deja el mismo resultado.
2. Si borra o pisa datos, primero los copia a `<tabla>_backup_<revisión>` en la
   misma migración; el `downgrade` restaura desde ahí.
3. Tiene test de ida y vuelta.
4. Expand/contract: agregar y rellenar ahora, borrar lo viejo en otro PR.

## Revertir en producción

1. **Antes** de aplicar una migración de datos, crear una branch en Neon (copia
   instantánea de la base) y anotar acá el nombre y la hora.
2. Si falla `alembic upgrade head` (corre al arrancar el contenedor, no como
   pre-deploy: ver [deploy.md](deploy.md)), el contenedor nuevo no levanta y
   Render sigue sirviendo la versión anterior. Arreglás la migración y
   volvés a desplegar; no hace falta tocar la base.
3. Si la migración se aplicó y el problema aparece después:

   ```bash
   alembic downgrade -1     # desde la consola de Render
   ```

   y volver a desplegar el commit anterior.
4. Si el downgrade no alcanza (datos perdidos), restaurar desde la branch de Neon
   del paso 1.
5. Anotar qué pasó en la minuta de la semana: es material del informe final.

## Cambiar de motor de base

Si en el futuro se mueve el grafo o los vectores a otro motor: cada módulo expone
export/import de sus datos a archivos, y el SQL crudo vive solo adentro del
módulo dueño. La migración es exportar, cambiar la implementación de ese módulo e
importar, sin tocar agentes ni canales.

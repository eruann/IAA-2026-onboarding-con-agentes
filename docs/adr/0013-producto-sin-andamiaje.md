# 0013 — El producto funciona sin el andamiaje

- Fecha: 2026-11-03
- Estado: aceptada
- Decide: Tech Lead

## Contexto

El andamiaje (talleres, guías, dibujo del grafo) ayuda al equipo a construir el
producto, pero no se entrega. La idea es poder sacarlo al final borrando sus
archivos, sin tocar el producto. Una prueba borrándolo en una copia mostró que no
se podía: la app no importaba, las migraciones fallaban (y en Render corren antes
de arrancar) y los tests no llegaban a correr. El producto dependía del andamiaje
en cinco lugares: `llm/` exportaba la lista de modelos (`catalog.py`, marcado
como andamiaje pero usado por las pantallas y configurado en Render), `agents/`
exportaba el dibujo del grafo, `ui/__init__.py` cargaba siempre los talleres, la
entrada tenía adentro el botón de los talleres y dos tests de producto usaban
una función de los talleres. El test que debía controlarlo vivía en un archivo
de andamiaje y miraba poco.

## Decisión

El producto nunca importa andamiaje; el andamiaje puede importar lo que necesite.
`llm/catalog.py` pasa a ser producto. Lo que el andamiaje suma a una pantalla del
producto se engancha desde afuera: `ui/__init__.py` carga los talleres solo si
existen y el botón de los talleres lo agrega `ui/pages.py` a `ENTRY_EXTRAS` de la
entrada. Dos tests en `file_tags_test.py`, que no es de ningún módulo y sobrevive
al borrado, lo controlan: uno busca imports del producto (y de sus tests) a
módulos de andamiaje, y el otro borra el andamiaje en una copia e importa todo lo
que queda.

## Consecuencias

- Sacar el andamiaje es borrar archivos: el producto arranca igual y
  `/ui/talleres` deja de existir.
- Un PR que haga depender al producto del andamiaje falla en CI con el archivo y
  la línea.
- Quedan restos inofensivos que se pueden limpiar al borrar: la clave
  `test_key` de la sesión, los parámetros de `chat()` y `sidebar()` que solo usan
  los talleres y `ADMIN_PASSWORD` en `config.py`.
- Las funciones que el producto exporta solo para los talleres (por ejemplo,
  `game.review_rows`) siguen en el producto: son chicas y no rompen nada si
  quedan sin usar.

## Alternativas descartadas

- **Sacar el selector de modelo de las pantallas** para que `catalog.py` pueda
  seguir siendo andamiaje: el selector ya es parte de la demo y Render lo
  configura.
- **Un script aparte que borre el andamiaje y corra todo:** controla lo mismo
  que el test de la copia, pero nadie lo corre si no está en la suite.

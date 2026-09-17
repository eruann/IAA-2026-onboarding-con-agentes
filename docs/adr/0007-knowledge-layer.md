# 0007 — Knowledge layer: documentos y red informal detrás de una sola puerta

- Fecha: 2026-09-16
- Estado: aceptada
- Decide: el equipo

## Contexto

Muchas empresas están concentrando todo lo que la organización sabe en una
**knowledge layer**: una capa única que cualquier aplicación puede consultar, en
vez de que cada sistema tenga su propio pedazo de conocimiento.

El sistema ya tenía las dos piezas de esa capa, pero como módulos sueltos y al
mismo nivel que el juego: `rag` (documentos) y `knowledge` (el grafo de quién
sabe qué). `agents` llamaba a cada uno por separado, y la regla prohibía que se
hablaran entre sí.

Además, el grafo no mapea el organigrama: captura las relaciones extraoficiales
que la organización no registra en ningún lado.

## Decisión

El sistema construye una knowledge layer, por ahora restringida al onboarding.

- Paquete `src/onboarding/knowledge/` con dos partes:
  - `rag`: **lo escrito** (manuales, políticas, procesos).
  - `informal_network`: **lo no escrito**, la red informal: quién sabe de qué y
    a quién se consulta de verdad, más allá del organigrama. Reemplaza al módulo
    `knowledge` anterior; el nombre sigue el término establecido en análisis de
    redes organizacionales.
- **Una sola puerta**: fuera de la capa se importa solo desde
  `onboarding.knowledge`.
- Adentro de la capa, `rag` e `informal_network` sí pueden cruzarse (un proceso
  documentado con la persona que de verdad lo maneja), por clave y sin foreign
  keys.
- `game`, `bot` y `api` no son parte de la capa: son la primera aplicación que la
  usa. Leen de ella y escriben en ella a través de `agents`.

## Consecuencias

- La capa tiene identidad propia en el código, no solo en los diagramas: otra
  aplicación podría consumirla mañana sin tocar el onboarding.
- `agents` depende de una interfaz en lugar de dos, y no sabe si una respuesta
  sale de un documento o de la red informal.
- El "no sé, preguntale a X" queda en su lugar natural: el cruce entre lo escrito
  y lo no escrito ocurre adentro de la capa.
- Rutas nuevas: `knowledge/rag/`, `knowledge/informal_network/`,
  `eval/informal_network_ground_truth.yaml`. La ingesta ahora es
  `python -m onboarding.knowledge.rag corpus`.
- Los roles no cambian: RAG y evaluación es dueño de lo escrito; Grafo cultural y
  datos, de lo no escrito. La puerta (`knowledge/__init__.py`) es de los dos.
- La puerta es un archivo que tocan dos roles: cambios en su interfaz se avisan
  como en los archivos compartidos.

## Alternativas descartadas

- **Agrupar solo en los diagramas**, dejando `rag` y el grafo sueltos: cero
  movimiento de código, pero la capa no existe como interfaz y cada consumidor
  depende de sus partes internas.
- **Nombres para la red informal**: `org_graph` (sugiere el organigrama, justo lo
  que no es), `people_relationship_graph` (largo y no transmite lo
  extraoficial), `tacit_network` (menos conocido), `shadow_org` (suena a
  vigilancia, el riesgo que la propuesta quiere evitar).

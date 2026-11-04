> **andamiaje**
>
> Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
> construya, pruebe o entienda el producto (talleres, diagramas, guías).
> No es parte del producto.

# Taller Grafo cultural y datos

**Tu parte:** lo no escrito, quién sabe qué más allá del organigrama.

## Qué construís y qué trae el taller

**Lo construís vos:**

- `agents/extract_knowledge/` → tu agente, igual que los demás: `node.py` junta
  su contexto y le contesta a la persona con su prompt, `prompt.md`
  (`ask_model`). Su contexto son las relaciones que saca `extract_triples`, cada
  una con la frase que la respalda (**ya funciona**), con sus propias
  instrucciones en `extraction_prompt.md`.
- `knowledge/informal_network/triples.py` → `KnowledgeTriple`: la forma de una
  relación, lo que el resto del sistema usa de tu parte.
- `knowledge/informal_network/queries.py` → `who_knows_about`: pendiente.
- `knowledge/informal_network/models.py`: las tablas `nodes` y `edges`. Pendiente.

**Lo trae el taller** (`workshop.py`, en esta carpeta): el chat con tu agente y
las pruebas, en las tres secciones de siempre: `extract_triples` sale de tu
agente y `who_knows_about`, de la knowledge layer. Todavía no tenés pruebas ad
hoc: cuando hagan falta (por ejemplo, medir la cobertura), van en `checks.py`.

## Qué falta

1. Tablas `nodes` y `edges` con su migración (`informal_network/models.py`).
2. Guardar las relaciones que encuentra tu agente en esas tablas.
3. `who_knows_about()`: a quién preguntarle por un tema. La va a usar el
   agente de RAG para derivar cuando no hay documentación.
4. Medir la cobertura contra `eval/informal_network_ground_truth.yaml`.

## Qué probar en el taller

- **Chat**: escribile a tu agente una conversación ("Para Excel avanzado,
  preguntale a Diego Fernández") y te devuelve las relaciones que encontró, con
  su respaldo. El panel **Grafo** marca el recorrido por `extract_knowledge`.
  Elegí un modelo con salida estructurada: con el `fake` falla.
- **Extraer relaciones**: lo mismo, llamando a `extract_triples` directo. Podés
  comparar dos modelos lado a lado. Necesita un modelo con salida estructurada.
- **¿Quién sabe de?**: aparece como pendiente hasta que lo implementes.

## Pedidos de plan para Claude Code o Codex

Prendé el modo plan (Claude Code: `Shift+Tab` hasta *plan mode*; Codex:
`/plan`; más detalle en `DEVELOPMENT.md`, "Primero el plan") y pedí, por
ejemplo:

- `Armame un plan para crear las tablas nodes y edges (informal_network/models.py) con su migración. Explicame cada columna y para qué sirve.`
- `Armame un plan para que mi agente (agents/extract_knowledge) guarde las relaciones en nodes/edges. ¿Qué archivos toca y cómo lo pruebo?`
- `Armame un plan para implementar who_knows_about() sobre nodes/edges. ¿Cómo ordena a las personas y por qué?`
- `Armame un plan para sumar a mi taller una prueba que muestre la cobertura contra el ground truth.`

Leé el plan, preguntá lo que no entiendas y recién ahí aprobalo.

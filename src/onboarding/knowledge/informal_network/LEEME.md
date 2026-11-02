> **andamiaje**
>
> Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
> construya, pruebe o entienda el producto (talleres, diagramas, guías).
> No es parte del producto.

# Taller Grafo cultural y datos

**Tu parte:** lo no escrito, quién sabe qué más allá del organigrama.

- `extract_triples` (`knowledge/informal_network/extraction.py`): saca
  relaciones de un texto, con la frase que las respalda. **Ya funciona.**
- Tu nodo, `agents/extract_knowledge/node.py`: usa `extract_triples`.
- `who_knows_about` (`knowledge/informal_network/queries.py`): pendiente.

## Qué falta

1. Tablas `nodes` y `edges` con su migración (`informal_network/models.py`).
2. Guardar las relaciones que encuentra tu nodo en esas tablas.
3. `who_knows_about()`: a quién preguntarle por un tema. La va a usar el
   agente de conocimiento para derivar cuando no hay documentación.
4. Medir la cobertura contra `eval/informal_network_ground_truth.yaml`.

## Cómo probar

- **Extraer relaciones**: pegás un texto y ves las relaciones con su respaldo.
  Podés comparar dos modelos lado a lado.
- **¿Quién sabe de?**: aparece como pendiente hasta que lo implementes.
- **Chat**: el agente de onboarding responde sobre el organigrama y Tesorería.

## Cómo pedírselo a Claude Code o Codex: primero el plan

No le pidas que lo haga de una: pedile un **plan** y entendelo antes de
aprobarlo. Prendé el modo plan (Claude Code: `Shift+Tab` hasta *plan mode*;
Codex: `/plan`; más detalle en `DEVELOPMENT.md`, "Primero el plan") y pedí, por
ejemplo:

- `Armame un plan para crear las tablas nodes y edges (informal_network/models.py) con su migración. Explicame cada columna y para qué sirve.`
- `Armame un plan para que el nodo agents/extract_knowledge guarde las relaciones en nodes/edges. ¿Qué archivos toca y cómo lo pruebo?`
- `Armame un plan para implementar who_knows_about() sobre nodes/edges. ¿Cómo ordena a las personas y por qué?`
- `Armame un plan para sumar a mi taller una prueba que muestre la cobertura contra el ground truth.`

Leé el plan, preguntá lo que no entiendas y recién ahí aprobalo. Si no podés
explicar con tus palabras qué va a cambiar, todavía no lo apruebes.

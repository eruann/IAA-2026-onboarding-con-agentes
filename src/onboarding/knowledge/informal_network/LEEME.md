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

## Pedidos listos para Claude Code o Codex

- `Creá las tablas nodes y edges de knowledge/informal_network/models.py con su migración y downgrade.`
- `Hacé que el nodo agents/extract_knowledge guarde las relaciones en nodes/edges, con test db.`
- `Implementá who_knows_about() sobre nodes/edges, con test db.`
- `Agregá a mi taller (knowledge/informal_network/workshop.py) una prueba que muestre la cobertura contra el ground truth.`

# Taller Grafo: lo no escrito

**Tu nodo:** Red informal (`agents/extract_knowledge/node.py`). Corre al final
de **todas** las conversaciones y no le contesta al usuario: extrae quién sabe
qué y lo guarda.

**Tu parte de la knowledge layer:** `knowledge/informal_network/`
(`extract_triples`, `who_knows_about`, tablas `nodes` y `edges`).

## Qué falta

1. Tablas `nodes` y `edges` con su migración (`informal_network/models.py`).
2. `who_knows_about()` en `informal_network/queries.py`: hoy está pendiente. La
   usa el agente Conocimiento para derivar.
3. El nodo `extract_knowledge` llamando a `extract_triples` y guardando las
   relaciones con su frase de respaldo.
4. Cobertura contra `eval/informal_network_ground_truth.yaml`.

## Cómo probar

- **Extraer relaciones**: pegás una conversación y ves las relaciones con su
  frase de respaldo. Podés comparar dos modelos lado a lado.
- **¿Quién sabe de?**: lo que respondería la red para un tema.
- **El chat**: cualquier mensaje pasa por tu nodo al final; mirá el recorrido.

## Pedidos listos para Claude Code o Codex

- `Creá las tablas nodes y edges de knowledge/informal_network/models.py con su migración y downgrade.`
- `Implementá who_knows_about() sobre nodes/edges, con test db.`
- `Agregá a mi taller (knowledge/informal_network/workshop.py) una prueba que muestre la cobertura contra el ground truth.`

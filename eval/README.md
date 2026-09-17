# Evaluación

La propuesta promete números, no impresiones. Acá viven los sets fijos contra los
que se mide.

| Archivo | Qué mide | Titular |
|---|---|---|
| `rag_questions.yaml` | precisión y recall del retrieval | RAG |
| `informal_network_ground_truth.yaml` | cobertura de la red informal | Grafo |
| `baseline/` | el mismo onboarding hecho a mano, con horas registradas | PM |

## Reglas

1. **Los sets se definen antes de correr el experimento.** Si se ajustan después
   de ver los resultados, la medición no vale.
2. El retrieval se mide **aparte** de la calidad de la respuesta: así se puede
   distinguir "no encontró el documento" de "encontró y respondió mal".
3. Las corridas escriben en `eval/runs/` (ignorada por git). En el repo se
   versiona el resumen, no la corrida completa.
4. Estas corridas **gastan plata**: usan un modelo real. No corren en CI; los
   tests marcados `@pytest.mark.llm` quedan afuera a propósito.

## Métricas del TP

- Horas-persona de la organización por ingresante, contra el baseline manual.
- Días simulados hasta completar un conjunto fijo de hitos.
- Precisión/recall del retrieval.
- Cobertura del grafo: nodos y relaciones capturadas contra el ground truth.
- Costo y latencia por interacción (sale de la tabla `llm_calls`).

# 0006 — Acceso a modelos vía OpenRouter

- Fecha: 2026-09-15
- Estado: aceptada
- Decide: dueño del repo + rol Agentes

## Contexto

La propuesta se compromete a justificar la elección de modelo con datos de costo
y latencia, y a poder medir contra un modelo abierto. Además, los tests no tienen
que depender de ningún proveedor ni gastar plata. El ADR 0001 dejó Claude como
default con "capa de proveedor intercambiable"; falta definir cómo se
intercambia.

## Decisión

Todo el acceso a modelos pasa por `onboarding.llm.get_chat_model()`, que devuelve
un chat model de LangChain según dos variables de entorno:

| `LLM_PROVIDER` | Para qué |
|---|---|
| `fake` | tests y CI: respuestas fijas, sin red ni costo. Es el default |
| `openrouter` | desarrollo y demo: una sola API key para Claude, GPT, Llama, Qwen |
| `openai_compat` | modelo abierto self-host (Ollama), misma interfaz |

OpenRouter expone una API compatible con OpenAI, así que se usa el mismo cliente
apuntando a otra URL base. Cambiar de modelo es cambiar `LLM_MODEL`
(`anthropic/claude-haiku-4.5`, `openai/gpt-4o-mini`, `qwen/...`).

## Consecuencias

- Comparar dos modelos en la evaluación es cambiar una variable de entorno, sin
  tocar código: exactamente lo que la propuesta promete medir.
- Una sola cuenta y una sola key para todo el equipo, en vez de una por
  proveedor.
- CI no depende de la red ni de una key, y no puede gastar plata por accidente.
- Ningún módulo puede nombrar un proveedor: si aparece un `import anthropic` en
  un PR, está mal.
- Se depende de un intermediario más (si OpenRouter se cae, se cambia
  `LLM_PROVIDER` a `openai_compat` o al proveedor directo).
- OpenRouter no da embeddings: eso va por separado (ADR 0005).

## Alternativas descartadas

SDK de Anthropic directo: ata el código a un proveedor y obliga a escribir una
capa propia para comparar modelos, que es justo lo que este ADR evita.

# 0009 — Interfaz web con NiceGUI y un taller por rol

- Fecha: 2026-11-02
- Estado: aceptada
- Decide: Tech Lead

## Contexto

Cada rol trabajaba sobre una pieza suelta (una función, un nodo) sin poder ver el
resultado ni probarla con un modelo real. La primera interfaz del proyecto fue un
prototipo en Streamlit (PR #15): un chat con el agente y una prueba de la
extracción de relaciones. Mostró que tener una pantalla para probar cambia todo,
pero corría aparte, creaba clientes de modelo a mano y leía claves de un archivo
local.

Streamlit trae su propio servidor web: no se puede montar dentro de la app
FastAPI, y en Render necesitaría un segundo servicio.

## Decisión

La interfaz es **NiceGUI montado en la misma app FastAPI**, en `/ui`
(`src/onboarding/ui/`): un solo proceso y un solo servicio. Usa los agentes por
`agents.run_turn` y los modelos por `llm.get_chat_model` y
`llm.available_models` (el del `.env`, los gratis de OpenRouter y los de Ollama).

La interfaz se organiza en **talleres, uno por rol**. Cada rol declara el suyo en
un `workshop.py` de su carpeta (`onboarding/workshop.py`): a qué nodo va el chat y
qué funciones propias se prueban sueltas. El formulario de cada prueba se arma
solo con la firma de la función, así nadie tiene que aprender NiceGUI para sumar
una prueba. El panel del jefe sigue en HTMX (`api/`).

## Consecuencias

- Cada rol prueba su parte con un modelo real, gratis (OpenRouter `:free` u
  Ollama), y ve qué le falta: las funciones sin implementar aparecen como
  pendientes con su archivo.
- Sumar una prueba es escribir una función con tipos y listarla.
- Una dependencia nueva (`nicegui`) y una variable nueva (`UI_STORAGE_SECRET`).
- Dos tecnologías de interfaz: NiceGUI (`/ui`, la mantiene el Tech Lead) y HTMX
  (`/panel`, Experiencia).
- Pendiente: talleres de los demás roles, el dibujo del grafo con el recorrido de
  cada mensaje y la entrada eligiendo una persona de la empresa.

## Alternativas descartadas

- **Streamlit**: un segundo servicio en Render (y dos URLs) porque no se monta
  en FastAPI.
- **Chainlit / Gradio**: se montan en FastAPI, pero están pensados para un chat o
  una demo de una función; los talleres con varias pruebas y selectores quedan
  forzados.
- **Todo en HTMX como el panel**: una sola tecnología, pero cada prueba nueva es
  HTML a mano; el formulario automático sale mucho más simple en Python.

# Talleres: cómo armar el tuyo

Cada rol tiene un **taller** en la interfaz web (`http://localhost:8000/ui/`):
un chat con un agente del grafo, **pruebas** de sus propias funciones (sin pasar
por el agente) y su **guía**. El porqué está en
[ADR 0009](adr/0009-interfaz-nicegui-y-talleres.md); acá, cómo se arma.

No hace falta saber nada de la interfaz (NiceGUI): el taller se declara en un
archivo `workshop.py` de la carpeta de tu rol, y el formulario de cada prueba
sale solo de la firma de la función.

## Lo que ya existe

| Rol | Taller | Guía |
|---|---|---|
| Grafo cultural y datos | [`knowledge/informal_network/workshop.py`](../src/onboarding/knowledge/informal_network/workshop.py) | [`LEEME.md`](../src/onboarding/knowledge/informal_network/LEEME.md) |
| RAG, Experiencia, Agentes, Tech Lead | Todavía no: aparecen como "próximamente" en el selector de talleres | |

## El archivo `workshop.py`

Es Python, pero solo declara cosas: no lleva lógica. El del Grafo:

```python
from pathlib import Path

from onboarding.knowledge.informal_network.extraction import extract_triples
from onboarding.knowledge.informal_network.queries import who_knows_about
from onboarding.workshop import Tool, Workshop

WORKSHOP = Workshop(
    role="Grafo cultural y datos",
    intent="answer_question",
    summary="Lo no escrito: quién sabe qué, más allá del organigrama. ...",
    tools=(
        Tool(extract_triples, "Extraer relaciones", "Pegá una conversación. Ej.: ..."),
        Tool(who_knows_about, "¿Quién sabe de?", "Escribí un tema: a quién derivaría el agente."),
    ),
    guide=Path(__file__).parent / "LEEME.md",
)
```

| Campo | Qué es |
|---|---|
| `role` | Nombre del rol, igual que en [docs/roles.md](roles.md). Es el nombre del taller en el selector. |
| `intent` | A qué nodo del grafo va el chat del taller. Uno de los valores de `Intent` en [`agents/state.py`](../src/onboarding/agents/state.py): `answer_question`, `generate_quest`, `validate_evidence` o `extract_knowledge`. |
| `summary` | Una o dos líneas: qué construye el rol. Se muestra debajo del título. |
| `tools` | Las pruebas: una línea `Tool(función, "Título", "Ayuda corta")` por función. |
| `guide` | El `LEEME.md` de al lado, que se muestra en la sección **Guía**. |

## Sumar una prueba

1. Escribí la función en el módulo de tu rol, con **tipo en todos los
   parámetros** (ver la tabla de abajo).
2. Sumala a `tools`: `Tool(mi_funcion, "Título", "Ayuda corta")`.
3. Escribí su test al lado, como siempre (`<modulo>_test.py`).

Listo: al recargar la página aparece una tarjeta nueva en **Pruebas**, con un
campo por parámetro y el botón **Probar**.

### Qué campo dibuja cada tipo

| Tipo del parámetro | Campo en pantalla |
|---|---|
| `str` | Caja de texto |
| `int` | Número entero |
| `float` | Número con decimales |
| `bool` | Interruptor |
| `Literal["a", "b"]` | Selector con esas opciones |
| `BaseChatModel \| None` | Selector de modelo, con la opción **Comparar con otro modelo** (dos resultados lado a lado) |

- Un parámetro con valor por defecto es opcional y el campo arranca con ese valor.
- `X | None` se dibuja como `X`.
- Si un parámetro no tiene tipo, o tiene uno que no está en la tabla,
  `workshop_test.py` falla con un mensaje que dice cuál.

### Cómo se muestra el resultado

| La función devuelve | Se ve |
|---|---|
| `str` | Texto (acepta Markdown) |
| Lista de dataclasses o de dicts | Tabla, una fila por elemento |
| Otra lista | Lista con viñetas |
| Un dataclass o un dict | JSON |
| `None` o lista vacía | "Sin resultados." |

### Funciones pendientes y errores

- Si la función todavía es un TODO (su cuerpo hace `raise NotImplementedError`),
  la tarjeta muestra **pendiente** y, al probarla, en qué archivo y línea se
  completa. Sirve para sumar la prueba desde el primer día.
- Si falla el modelo (key inválida, límite gratis, Ollama apagado...), el error
  se explica en castellano en vez de mostrar el traceback.

## Crear el taller de un rol nuevo

1. En la carpeta del rol, crear `workshop.py` (con `WORKSHOP = Workshop(...)`)
   y `LEEME.md` (qué construye el rol, qué falta, cómo probar y pedidos de plan
   de ejemplo).
2. Exportar `WORKSHOP` por la interfaz pública del módulo (su `__init__.py`).
3. Sumarlo en `all_workshops()` de [`onboarding/workshop.py`](../src/onboarding/workshop.py)
   y sacar el rol de `UPCOMING`.
   - Los roles de la knowledge layer (RAG) entran por `WORKSHOPS` en
     `knowledge/__init__.py`, que es un archivo compartido: avisalo en el PR.
4. Correr los tests: `workshop_test.py` revisa que todas las pruebas de todos los
   talleres se puedan dibujar y que la guía exista.

## Pedírselo a Claude Code o Codex

Los dos leen [AGENTS.md](../AGENTS.md), que los manda a esta guía. Usá el modo
plan ([cómo](../DEVELOPMENT.md#primero-el-plan)) y pedí, por ejemplo:

- `Armame un plan para sumar a mi taller una prueba de <función>. ¿Qué tipos tienen que tener sus parámetros?`
- `Armame un plan para crear el taller de mi rol (<rol>) siguiendo docs/talleres.md.`
- `¿Cómo se va a ver en el taller el resultado de <función>? Explicámelo sin cambiar nada.`

ChatGPT en la web no ve el repo: para esto usá Codex o Claude Code, que trabajan
sobre tus archivos.

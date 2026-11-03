# Talleres: cómo armar el tuyo

Cada rol tiene un **taller** en la interfaz web: entrá a
`http://localhost:8000/ui/` y tocá **Talleres (Test)** (en tu compu entra
directo; en la demo de Render pide `ADMIN_PASSWORD`). Cada taller tiene un chat
con un agente del grafo, **pruebas** de sus propias funciones (sin pasar
por el agente) y su **guía**. El porqué está en
[ADR 0009](adr/0009-interfaz-nicegui-y-talleres.md); acá, cómo se arma.

No hace falta saber nada de la interfaz (NiceGUI): el taller se declara en el
`workshop.py` de la carpeta de tu agente (`agents/<nodo>/`), y el formulario de
cada prueba sale solo de la firma de la función. Todos los talleres tienen la
misma forma ([ADR 0012](adr/0012-taller-en-la-carpeta-del-agente.md)): si sabés
usar uno, sabés usar los demás.

## Lo que ya existe

| Rol | Taller | Guía |
|---|---|---|
| Agentes y orquestación | [`agents/workshop.py`](../src/onboarding/agents/workshop.py) | [`LEEME.md`](../src/onboarding/agents/LEEME.md) |
| RAG y evaluación | [`agents/answer_question/workshop.py`](../src/onboarding/agents/answer_question/workshop.py) | [`LEEME.md`](../src/onboarding/agents/answer_question/LEEME.md) |
| Grafo cultural y datos | [`agents/extract_knowledge/workshop.py`](../src/onboarding/agents/extract_knowledge/workshop.py) | [`LEEME.md`](../src/onboarding/agents/extract_knowledge/LEEME.md) |
| Experiencia | [`agents/validate_evidence/workshop.py`](../src/onboarding/agents/validate_evidence/workshop.py) | [`LEEME.md`](../src/onboarding/agents/validate_evidence/LEEME.md) |
| Diseñador de misiones | [`agents/generate_quest/workshop.py`](../src/onboarding/agents/generate_quest/workshop.py) | [`LEEME.md`](../src/onboarding/agents/generate_quest/LEEME.md) |

## El archivo `workshop.py`

Es Python, pero solo declara cosas: no lleva lógica. Las pruebas salen de tres
lugares, y se importan siempre en tres secciones, con estos encabezados y en este
orden (un test lo revisa; una sección vacía lleva `# (ninguna)`):

| Sección | De dónde sale la prueba | En la tarjeta |
|---|---|---|
| `# 1. Pruebas ad hoc` | el `checks.py` de tu agente: funciones armadas solo para probar o medir en el taller (andamiaje) | «prueba ad hoc» |
| `# 2. Del agente` | el `node.py` de tu agente (producto) | «de tu agente» |
| `# 3. Del código común` | la knowledge layer, `game` y demás interfaces (producto: no se mudan, se llaman) | «código común» |

`checks.py` está siempre, aunque esté vacío, y una prueba ad hoc nueva lleva su
test en `checks_test.py`. El taller no importa nunca de la carpeta de otro agente.
El del Grafo:

```python
from pathlib import Path

# 1. Pruebas ad hoc (andamiaje): checks.py de este agente
# (ninguna)
# 2. Del agente (producto): node.py de este agente
from onboarding.agents.extract_knowledge.node import extract_triples

# 3. Del código común (producto): knowledge layer, game y demás interfaces
from onboarding.knowledge import who_knows_about
from onboarding.workshop import Tool, Workshop

WORKSHOP = Workshop(
    role="Grafo cultural y datos",
    intent="extract_knowledge",
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
| `intent` | A qué nodo del grafo va el chat del taller. Uno de los valores de `Intent` en [`agents/state.py`](../src/onboarding/agents/state.py): `answer_question`, `generate_quest`, `validate_evidence` o `extract_knowledge`. `None`: decide el coordinador (el taller de Agentes). |
| `summary` | Una o dos líneas: qué construye el rol. Se muestra debajo del título. |
| `tools` | Las pruebas: una línea `Tool(función, "Título", "Ayuda corta")` por función. |
| `guide` | El `LEEME.md` de al lado, que se muestra en la sección **Guía**. |
| `greeting` | Opcional. Lo primero que dice el chat: qué escribirle a tu agente (p. ej. «Pegame una conversación…»). Sin él, el chat usa el saludo general, pensado para preguntas sobre la empresa. |
| `embeds` | Opcional. Páginas de la app que construye el rol y se ven dentro del taller, cada una en su sección con botón **Recargar**: `Embed("Panel del jefe", "/panel", "Ayuda corta")`. Un test revisa que la ruta exista. |

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
| `Literal["a", "b"]` | Selector con esas opciones (sin valor por defecto, arranca en la primera) |
| `BaseChatModel \| None` | Selector de modelo, con la opción **Comparar con otro modelo** (dos resultados lado a lado) |
| `ChatHistory` | No se dibuja: recibe la conversación del chat del taller, como tupla de `(quién, texto)` |

- Un parámetro con valor por defecto es opcional y el campo arranca con ese valor.
- `X | None` se dibuja como `X`.
- Si un parámetro no tiene tipo, o tiene uno que no está en la tabla,
  `workshop_test.py` falla con un mensaje que dice cuál.

### Cómo se muestra el resultado

| La función devuelve | Se ve |
|---|---|
| `str` | Texto (acepta Markdown) |
| `bool` | ✅ Sí / ❌ No |
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

- Si un mensaje del **chat** falla por el modelo, su globo ofrece **Usar otro
  modelo (Auto)**, que pasa al siguiente de la lista y cambia el selector, y
  **Usar otro modelo (manual)**, que reintenta con el que elijas en la barra
  lateral. Los botones valen mientras ese mensaje sea lo último de la
  conversación.

### Qué marca el grafo

El panel **Grafo** (arriba a la derecha) marca en rojo por dónde pasó el último
mensaje del chat; si falló, llega hasta el nodo donde falló y le pone el borde
rojo punteado. Cuando corrés una prueba, marca en violeta las funciones de la
knowledge layer que usa (sale del mismo análisis del código que dibuja el
grafo). Nada de esto se configura por taller.

## Crear el taller de un rol nuevo

1. En la carpeta de su agente (`agents/<nodo>/`), crear `workshop.py` (con
   `WORKSHOP = Workshop(...)`, solo la declaración y las tres secciones),
   `checks.py` (aunque esté vacío) y `LEEME.md` con las mismas secciones que los
   demás: "Qué construís y qué trae el taller", "Qué falta", "Qué probar en el
   taller" y "Pedidos de plan". Los tres son andamiaje: empiezan con la marca
   `andamiaje` y su leyenda ([AGENTS.md](../AGENTS.md#producto-y-andamiaje)).
2. Sumar el rol a `ROLE_ORDER` en [`onboarding/workshop.py`](../src/onboarding/workshop.py)
   (el orden del selector) y sacarlo de `UPCOMING`. No hay que exportarlo: la
   interfaz busca el `workshop.py` de cada agente de `NODES` (`workshop_modules`).
3. Correr los tests: `workshop_test.py` revisa que todas las pruebas se puedan
   dibujar, que la guía exista, que el orden sea el de `ROLE_ORDER` y que los
   imports estén en sus tres secciones; `agents/graph_test.py`, que la carpeta del
   agente tenga todos sus archivos y no importe de otro agente.

## Pedírselo a Claude Code o Codex

Los dos leen [AGENTS.md](../AGENTS.md), que los manda a esta guía. Usá el modo
plan ([cómo](../DEVELOPMENT.md#primero-el-plan)) y pedí, por ejemplo:

- `Armame un plan para sumar a mi taller una prueba de <función>. ¿Qué tipos tienen que tener sus parámetros?`
- `Armame un plan para crear el taller de mi rol (<rol>) siguiendo docs/talleres.md.`
- `¿Cómo se va a ver en el taller el resultado de <función>? Explicámelo sin cambiar nada.`

ChatGPT en la web no ve el repo: para esto usá Codex o Claude Code, que trabajan
sobre tus archivos.

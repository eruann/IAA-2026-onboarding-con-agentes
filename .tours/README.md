# Recorridos guiados (CodeTour)

Cada `.tour` es un recorrido por el código que se abre en VS Code con la
extensión CodeTour. `bienvenida.tour` es el común; después hay uno por rol
(`pm`, `plataforma`, `agentes`, `rag`, `grafo`, `experiencia`, `comms`).

Los `.tour` se editan directo (son JSON). Lo más práctico es pedírselo a un
agente: "agregá un paso al recorrido de rag que muestre X". Este archivo es lo
que tiene que seguir para no romper nada.

## Cómo es un paso

```json
{
  "title": "Tu primer PR está acá",
  "file": "src/onboarding/agents/nodes.py",
  "pattern": "recorrido: nodo-respuesta$",
  "description": "Texto del paso...\n\n---\n\n(bloque de preguntas)"
}
```

- **Ubicación**: `file` + `pattern`, o `directory` (una carpeta), o nada (paso
  de solo texto, como el primero y el último de cada recorrido).
- **Marcador en el archivo**: en el código y en los `.yaml`, el paso apunta a un
  comentario `# recorrido: <nombre>` puesto justo arriba de lo que se muestra, y
  el `pattern` lo busca (`"recorrido: nodo-respuesta$"`). El nombre es único en
  todo el repo y no lleva rol: dos recorridos pueden usar el mismo marcador.
- **En los `.md`** no se ponen marcadores (en los prompts le llegarían al
  modelo): el `pattern` apunta a un título, por ejemplo `"^## Formato"`.
- **Nunca `line`**: un número de línea se corre con cualquier cambio en el
  archivo. Todo `pattern` tiene que encontrar **exactamente una** línea.
- **Texto**: 3 a 5 líneas, una sola idea, sin jerga. Quien lo lee no es dev.

Dentro del texto:

| Qué | Cómo |
|---|---|
| Link a un archivo | ``[`docs/roles.md`](./docs/roles.md)`` (ruta desde la raíz, empieza con `./`) |
| Link a otro recorrido | `[texto][Título exacto del tour]` |
| Botón que corre un comando | una línea que empiece con `>> ` (ej. `>> docker compose run --rm app pytest src/onboarding/knowledge/rag`) |
| Imagen | `![descripción](./.tours/img/archivo.png)` |

## El bloque de preguntas

Va al final del texto, después de `\n\n---\n\n`. Una o dos preguntas por paso
(la única excepción es el último paso de `bienvenida.tour`, que es el menú de
roles), siempre con este formato (respetá los textos, los usa todo el equipo):

```markdown
**Si usás Claude Code**, elegí dónde abrirlo:

- ¿Pregunta? [(side bar)](LINK_SIDEBAR) [(nueva ventana)](LINK_VENTANA)

**Si usás Codex:**

1. Copiá la pregunta:

- `Recorrido <nombre>: ¿Pregunta?`

2. [Abrir Codex con este código como contexto](command:chatgpt.addToThread)

3. Pegala en Codex y enviala.
```

- `<nombre>` es el nombre del archivo sin `.tour` (`agentes`, `rag`...). El
  prefijo `Recorrido <nombre>:` es lo que le avisa al agente que la pregunta
  viene de acá (ver la sección "Recorridos guiados" de `AGENTS.md`).
- En pasos sin `file`, el link de Codex es `[Abrir Codex](command:chatgpt.openSidebar)`.
- Codex no puede recibir texto desde un link: por eso la pregunta se copia a mano.

### Los links de Claude

Los dos llevan la pregunta **completa, con el prefijo** (`Recorrido <nombre>: ¿...?`),
codificada. Generalos con código (Python o Node, en Docker si no tenés local),
nunca a mano. Con `Q` = la pregunta completa:

```python
import json, urllib.parse as u


def enc(x):
    return u.quote(json.dumps(x, ensure_ascii=False), safe="")


LINK_SIDEBAR = "command:runCommands?" + enc(
    {
        "commands": [
            "claude-vscode.sidebar.open",
            {
                "command": "claude-vscode.editor.open",
                "args": ["", Q, None, None, False, {"programmatic": "honor-preferred-location"}],
            },
        ]
    }
)
LINK_VENTANA = "command:vscode.open?" + enc(
    ["vscode://anthropic.claude-code/open?prompt=" + u.quote(Q, safe="")]
)
```

Por qué así: `side bar` abre la barra lateral de Claude y después le pasa la
pregunta; `nueva ventana` usa el link `vscode://` de la extensión, que CodeTour
solo deja abrir a través de `vscode.open`. En los dos casos la pregunta queda
escrita, sin enviar.

## Antes de terminar

- El JSON es válido.
- Cada `pattern` encuentra una sola línea en su `file`.
- La pregunta dice lo mismo en los tres lugares (texto visible, links de Claude
  y la línea para copiar de Codex).
- Si agregaste un recorrido de rol nuevo: título `Rol: ...`, y su link en el
  último paso de `bienvenida.tour`.

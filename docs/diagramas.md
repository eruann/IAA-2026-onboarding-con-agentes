# Diagramas de arquitectura

Seis vistas, de lo general a lo particular.

Cómo verlos:

- **GitHub**: se dibujan solos.
- **VS Code**: extensión *Markdown Preview Mermaid Support*
  (`bierner.markdown-mermaid`) y `Ctrl+Shift+V`. Ver [setup.md](setup.md).
- **Para editarlos probando**: <https://mermaid.live>.

Convención en todos los diagramas:

- **Línea continua**: ya existe en el código.
- **Línea punteada**: diseñado, pendiente (`TODO(<rol>)`).

### Si agregás un diagrama

Todos tienen **fondo amarillo y líneas oscuras fijos**, para que se lean igual en
un editor claro o en uno oscuro. Para mantenerlo, copiá la estructura de uno
existente:

1. El bloque `%%{init: ...}%%` del principio: fija los colores de líneas y
   textos.
2. El fondo:
   - **flowchart**: todo adentro de `subgraph FONDO[" "]` con `direction` igual a
     la del diagrama, y al final
     `style FONDO fill:#fef9c3,stroke:#fef9c3`. Usá `TB` y no `TD`: dentro de un
     `subgraph`, Mermaid 11.12 (el de la extensión de VS Code) rechaza `TD`;
   - **sequenceDiagram**: los participantes adentro de `box rgb(254,249,195)` …
     `end`.

Títulos de recuadros (`subgraph`) **cortos**, de una o dos palabras: Mermaid
11.12 parte los largos en dos líneas y quedan encima de los nodos. El detalle va
en el texto debajo del diagrama.

No uses `erDiagram`, `classDiagram` ni otros tipos: Mermaid no les permite fondo
y en tema oscuro las líneas quedan invisibles. Las tablas se dibujan con
flowchart (ver el diagrama de datos). Tampoco sirve `themeCSS`: Mermaid 11
bloquea a propósito los estilos sobre el fondo.

---

## 1. Contexto: quién usa el sistema y con qué se conecta

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#fef9c3",
    "primaryColor": "#ffffff",
    "primaryTextColor": "#111827",
    "primaryBorderColor": "#374151",
    "secondaryColor": "#fde68a",
    "tertiaryColor": "#fffbeb",
    "lineColor": "#111827",
    "textColor": "#111827",
    "clusterBkg": "#fef3c7",
    "clusterBorder": "#b45309",
    "edgeLabelBackground": "#fef9c3",
    "noteBkgColor": "#fde68a",
    "noteTextColor": "#111827",
    "actorBkg": "#ffffff",
    "actorBorder": "#374151",
    "actorTextColor": "#111827",
    "actorLineColor": "#374151",
    "signalColor": "#111827",
    "signalTextColor": "#111827",
    "labelBoxBkgColor": "#ffffff",
    "labelTextColor": "#111827",
    "loopTextColor": "#111827"
  }
}}%%
flowchart LR
  %% Recuadro amarillo: fondo fijo, igual en editores claros y oscuros
  subgraph FONDO[" "]
    direction LR
    ING(["Ingresante"])
    JEFE(["Jefe / referente"])
    RRHH(["RRHH / Mesa de Ayuda"])

    subgraph SIS["Onboarding con agentes"]
      APP["App única<br/>API + panel + Slack"]
    end

    SLACK["Slack"]
    OR["OpenRouter<br/>Claude · GPT · Llama · Qwen"]
    PG[("Postgres + pgvector<br/>Neon en producción")]

    ING -- "misiones y preguntas" --> SLACK
    JEFE -- "aprueba con un clic" --> SLACK
    JEFE -- "ve progreso" --> APP
    RRHH -- "valida misiones" --> APP
    SLACK -- "POST /slack/events" --> APP
    APP -- "responde" --> SLACK
    APP --> OR
    APP --> PG
  end
  style FONDO fill:#fef9c3,stroke:#fef9c3
```

---

## 2. Módulos y dependencias: quién orquesta

Las flechas van **siempre hacia abajo**: una capa solo conoce a las de debajo.

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#fef9c3",
    "primaryColor": "#ffffff",
    "primaryTextColor": "#111827",
    "primaryBorderColor": "#374151",
    "secondaryColor": "#fde68a",
    "tertiaryColor": "#fffbeb",
    "lineColor": "#111827",
    "textColor": "#111827",
    "clusterBkg": "#fef3c7",
    "clusterBorder": "#b45309",
    "edgeLabelBackground": "#fef9c3",
    "noteBkgColor": "#fde68a",
    "noteTextColor": "#111827",
    "actorBkg": "#ffffff",
    "actorBorder": "#374151",
    "actorTextColor": "#111827",
    "actorLineColor": "#374151",
    "signalColor": "#111827",
    "signalTextColor": "#111827",
    "labelBoxBkgColor": "#ffffff",
    "labelTextColor": "#111827",
    "loopTextColor": "#111827"
  }
}}%%
flowchart TB
  %% Recuadro amarillo: fondo fijo, igual en editores claros y oscuros
  subgraph FONDO[" "]
    direction TB
    subgraph C1["1 · Canales"]
      direction LR
      API["<b>api</b><br/>FastAPI · panel HTMX<br/><i>punto de entrada</i>"]
      BOT["<b>bot</b><br/>Bolt · /slack/events"]
      SEED["<b>seed</b><br/>comando de carga"]
    end

    subgraph C2["2 · Orquestación"]
      AG["<b>agents</b><br/>grafo LangGraph<br/>★ orquestador principal"]
    end

    subgraph C3["3 · Dominio"]
      direction LR
      subgraph ONB["Onboarding"]
        GAME["<b>game</b><br/>misiones · puntos · canje"]
      end
      subgraph KL["Knowledge layer"]
        direction TB
        KAPI["<b>knowledge</b><br/>una sola puerta"]
        RAG["<b>rag</b><br/>lo escrito<br/>documentos · búsqueda · citas"]
        INF["<b>informal_network</b><br/>lo no escrito<br/>quién es quién"]
      end
    end

    subgraph C4["4 · Infraestructura"]
      direction LR
      LLM["<b>llm</b><br/>get_chat_model · costo"]
      DB["<b>db</b><br/>sesión · migraciones"]
    end

    API --> BOT
    API -.-> AG
    API -.-> GAME
    BOT -.-> AG
    BOT -.-> GAME
    SEED --> KAPI
    SEED -.-> GAME

    AG --> LLM
    AG -. "lee y escribe" .-> KAPI
    AG -.-> GAME

    KAPI --> RAG
    KAPI --> INF
    RAG <-. "se cruzan por key" .-> INF

    INF -.-> LLM
    RAG -.-> DB
    INF -.-> DB
    GAME -.-> DB

    LLM --> DB

    classDef orq fill:#fde68a,stroke:#b45309,stroke-width:2px,color:#1f2937
    class AG orq
    classDef puerta fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#111827
    class KAPI puerta
  end
  style FONDO fill:#fef9c3,stroke:#fef9c3
  style KL fill:#e0f2fe,stroke:#0369a1,stroke-width:2px
```

### La knowledge layer

Cada vez más empresas concentran todo lo que la organización sabe en una
**knowledge layer**: una capa única que cualquier aplicación puede consultar.
Este sistema la construye, por ahora restringida al onboarding.

Tiene dos fuentes y una sola puerta:

| Parte | Qué guarda | Titular |
|---|---|---|
| `knowledge.rag` | **Lo escrito**: manuales, políticas, procesos | RAG y evaluación |
| `knowledge.informal_network` | **Lo no escrito**: quién sabe de qué y a quién se consulta de verdad, lo que el organigrama no muestra | Grafo cultural y datos |
| `knowledge` | **La puerta**: lo único que el resto del sistema importa | los dos |

El onboarding (`game`, `bot`, `api`) no es parte de la capa: es **la primera
aplicación que la usa**. Lee de ella para responder y armar misiones, y escribe
en ella lo que extrae de cada conversación. Por eso la capa sirve más allá del
onboarding.

Para que se lea, quedan afuera dos dependencias que no aportan: `config`
(variables de entorno), que lo leen todos, y `api → db`, que se usa solo para
`/health/db`.

**Dos "orquestadores", dos responsabilidades:**

| Archivo | Rol | Qué decide |
|---|---|---|
| `api/main.py` → `create_app()` | **Punto de entrada** | Arma la aplicación: monta rutas, panel y Slack. No decide nada del negocio |
| `agents/graph.py` → `build_graph()` | **Orquestador principal** | Según la intención, qué pasos corren, en qué orden, y a qué módulos de dominio y a qué modelo llama |

Los canales (`api`, `bot`) reciben un pedido, se lo pasan a `agents` o a `game` y
devuelven la respuesta. Ninguno llama a la knowledge layer ni al modelo por su
cuenta.

**Reglas que el diagrama hace visibles:**

- Nada apunta hacia arriba: la knowledge layer no conoce a `agents`, `db` no
  conoce a `game`.
- `game` y la knowledge layer no se conectan entre sí: si uno necesita algo del
  otro, lo coordina `agents`.
- A la capa se entra **solo** por `knowledge` (`from onboarding.knowledge import
  retrieve`). Adentro, `rag` e `informal_network` sí se pueden cruzar (por
  ejemplo, un proceso documentado con la persona que de verdad lo maneja), por
  clave y sin foreign keys.
- Todo camino al modelo pasa por `llm`, que registra tokens y costo.

---

## 3. Adentro del orquestador: el grafo de LangGraph

### Hoy (`agents/graph.py`)

Cableado completo con nodos de prueba: cada intención llega a su nodo, que llama
al modelo con su prompt.

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#fef9c3",
    "primaryColor": "#ffffff",
    "primaryTextColor": "#111827",
    "primaryBorderColor": "#374151",
    "secondaryColor": "#fde68a",
    "tertiaryColor": "#fffbeb",
    "lineColor": "#111827",
    "textColor": "#111827",
    "clusterBkg": "#fef3c7",
    "clusterBorder": "#b45309",
    "edgeLabelBackground": "#fef9c3",
    "noteBkgColor": "#fde68a",
    "noteTextColor": "#111827",
    "actorBkg": "#ffffff",
    "actorBorder": "#374151",
    "actorTextColor": "#111827",
    "actorLineColor": "#374151",
    "signalColor": "#111827",
    "signalTextColor": "#111827",
    "labelBoxBkgColor": "#ffffff",
    "labelTextColor": "#111827",
    "loopTextColor": "#111827"
  }
}}%%
flowchart LR
  %% Recuadro amarillo: fondo fijo, igual en editores claros y oscuros
  subgraph FONDO[" "]
    direction LR
    S((START)) --> R{"_route<br/>según intent"}
    R -- generate_quest --> GQ["generate_quest"]
    R -- "answer_question<br/>(default)" --> AQ["answer_question"]
    R -- validate_evidence --> VE["validate_evidence"]
    R -- extract_knowledge --> EK["extract_knowledge"]
    GQ --> E((END))
    AQ --> E
    VE --> E
    EK --> E
  end
  style FONDO fill:#fef9c3,stroke:#fef9c3
```

### Diseño objetivo

Lo que cada nodo tiene que hacer cuando se implemente. Colores: **azul**, lo
escrito (`rag`); **verde**, la red informal; **rosa**, `game`. Azul y verde son
la knowledge layer, a la que siempre se entra por `knowledge`.

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#fef9c3",
    "primaryColor": "#ffffff",
    "primaryTextColor": "#111827",
    "primaryBorderColor": "#374151",
    "secondaryColor": "#fde68a",
    "tertiaryColor": "#fffbeb",
    "lineColor": "#111827",
    "textColor": "#111827",
    "clusterBkg": "#fef3c7",
    "clusterBorder": "#b45309",
    "edgeLabelBackground": "#fef9c3",
    "noteBkgColor": "#fde68a",
    "noteTextColor": "#111827",
    "actorBkg": "#ffffff",
    "actorBorder": "#374151",
    "actorTextColor": "#111827",
    "actorLineColor": "#374151",
    "signalColor": "#111827",
    "signalTextColor": "#111827",
    "labelBoxBkgColor": "#ffffff",
    "labelTextColor": "#111827",
    "loopTextColor": "#111827"
  }
}}%%
flowchart TB
  %% Recuadro amarillo: fondo fijo, igual en editores claros y oscuros
  subgraph FONDO[" "]
    direction TB
    S((START)) --> R{"intent"}

    R -- answer_question --> RET["knowledge.retrieve"]
    RET --> GEN["generar respuesta<br/>citando documento y sección"]
    GEN --> CHK{"knowledge.quote_is_supported"}
    CHK -- "sí" --> OK["respuesta + fuente"]
    CHK -- "no" --> WHO["knowledge.who_knows_about"]
    WHO --> DER["no tengo esta información,<br/>preguntale a X"]
    OK --> EXT
    DER --> EXT

    R -- validate_evidence --> VAL["evaluar evidencia"]
    VAL --> APR{"¿quién aprueba?"}
    APR -- agente --> GOK["game: aprobar y sumar puntos"]
    APR -- "jefe o mesa de ayuda" --> GPEND["game: pendiente<br/>de aprobación humana"]
    GOK --> EXT

    R -- generate_quest --> Q1["knowledge.retrieve<br/>documentación del rol"]
    Q1 --> Q2["knowledge: a quién involucrar"]
    Q2 --> Q3["game: guardar misión"]

    R -- extract_knowledge --> EXT["extraer relaciones<br/>de la conversación"]
    EXT --> SAVE["knowledge: guardar en la red informal<br/>con frase de respaldo"]

    SAVE --> E((END))
    Q3 --> E
    GPEND --> E

    classDef rag fill:#dbeafe,stroke:#1d4ed8,color:#1f2937
    classDef kg fill:#dcfce7,stroke:#15803d,color:#1f2937
    classDef game fill:#fce7f3,stroke:#be185d,color:#1f2937
    class RET,CHK,Q1 rag
    class WHO,Q2,SAVE kg
    class GOK,GPEND,Q3 game
  end
  style FONDO fill:#fef9c3,stroke:#fef9c3
```

Toda pregunta y toda aprobación terminan alimentando la red informal de la
knowledge layer: es el subproducto que diferencia la propuesta.

---

## 4. Flujos de punta a punta

### Pregunta del ingresante

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#fef9c3",
    "primaryColor": "#ffffff",
    "primaryTextColor": "#111827",
    "primaryBorderColor": "#374151",
    "secondaryColor": "#fde68a",
    "tertiaryColor": "#fffbeb",
    "lineColor": "#111827",
    "textColor": "#111827",
    "clusterBkg": "#fef3c7",
    "clusterBorder": "#b45309",
    "edgeLabelBackground": "#fef9c3",
    "noteBkgColor": "#fde68a",
    "noteTextColor": "#111827",
    "actorBkg": "#ffffff",
    "actorBorder": "#374151",
    "actorTextColor": "#111827",
    "actorLineColor": "#374151",
    "signalColor": "#111827",
    "signalTextColor": "#111827",
    "labelBoxBkgColor": "#ffffff",
    "labelTextColor": "#111827",
    "loopTextColor": "#111827"
  }
}}%%
sequenceDiagram
  autonumber
  %% Caja amarilla sobre todos los participantes: fondo fijo en editores claros y oscuros
  box rgb(254,249,195)
    actor I as Ingresante
    participant B as bot
    participant A as agents
    participant K as knowledge layer
    participant L as llm
  end
  I->>B: ¿cómo pido una compra?
  B-->>I: ack (antes de 3 segundos)
  B->>A: intent = answer_question
  A->>K: retrieve(pregunta)
  K-->>A: fragmentos con documento y sección (rag)
  A->>L: generar respuesta citando la fuente
  L-->>A: respuesta + cita
  A->>K: quote_is_supported(cita)
  alt la cita existe en el corpus
    A-->>B: respuesta + fuente
  else no hay soporte documental
    A->>K: who_knows_about(tema)
    K-->>A: persona sugerida (red informal)
    A-->>B: no tengo esta información, preguntale a X
  end
  B-->>I: mensaje en Slack
  Note over L: cada llamada queda en llm_calls<br/>(tokens, costo, latencia)
```

### Misión completada y aprobación

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#fef9c3",
    "primaryColor": "#ffffff",
    "primaryTextColor": "#111827",
    "primaryBorderColor": "#374151",
    "secondaryColor": "#fde68a",
    "tertiaryColor": "#fffbeb",
    "lineColor": "#111827",
    "textColor": "#111827",
    "clusterBkg": "#fef3c7",
    "clusterBorder": "#b45309",
    "edgeLabelBackground": "#fef9c3",
    "noteBkgColor": "#fde68a",
    "noteTextColor": "#111827",
    "actorBkg": "#ffffff",
    "actorBorder": "#374151",
    "actorTextColor": "#111827",
    "actorLineColor": "#374151",
    "signalColor": "#111827",
    "signalTextColor": "#111827",
    "labelBoxBkgColor": "#ffffff",
    "labelTextColor": "#111827",
    "loopTextColor": "#111827"
  }
}}%%
sequenceDiagram
  autonumber
  %% Caja amarilla sobre todos los participantes: fondo fijo en editores claros y oscuros
  box rgb(254,249,195)
    actor I as Ingresante
    actor J as Jefe
    participant B as bot
    participant A as agents
    participant G as game
    participant K as knowledge layer
  end
  I->>B: entrega evidencia
  B-->>I: ack
  B->>A: intent = validate_evidence
  A-->>G: recomendación: aprobada / revisión humana / incompleta
  G-->>J: misión pendiente con botón Aprobar (Slack o panel)
  J->>B: clic en Aprobar
  B->>G: aprobar (registra quién y cuándo)
  G-->>I: +puntos y nivel
  B->>A: intent = extract_knowledge sobre la conversación
  A->>K: relaciones para la red informal, con frase de respaldo
```

El registro de quién aprobó y cuándo es la base de la métrica del TP:
horas-persona de la organización por ingresante.

---

## 5. Datos: qué tabla es de quién

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#fef9c3",
    "primaryColor": "#ffffff",
    "primaryTextColor": "#111827",
    "primaryBorderColor": "#374151",
    "secondaryColor": "#fde68a",
    "tertiaryColor": "#fffbeb",
    "lineColor": "#111827",
    "textColor": "#111827",
    "clusterBkg": "#fef3c7",
    "clusterBorder": "#b45309",
    "edgeLabelBackground": "#fef9c3",
    "noteBkgColor": "#fde68a",
    "noteTextColor": "#111827",
    "actorBkg": "#ffffff",
    "actorBorder": "#374151",
    "actorTextColor": "#111827",
    "actorLineColor": "#374151",
    "signalColor": "#111827",
    "signalTextColor": "#111827",
    "labelBoxBkgColor": "#ffffff",
    "labelTextColor": "#111827",
    "loopTextColor": "#111827"
  }
}}%%
flowchart LR
  %% Recuadro amarillo: fondo fijo, igual en editores claros y oscuros
  subgraph FONDO[" "]
    direction LR

    subgraph GAME["game"]
      direction TB
      PEOPLE["<b>people</b><br/>key · slack_user_id<br/>area · is_newcomer"]
      QUESTS["<b>quests</b><br/>key · points · approver"]
      ASSIGN["<b>quest_assignments</b><br/>status · completed_at"]
      EVID["<b>evidence</b><br/>text · url"]
      APPR["<b>approvals</b><br/>approved_by · decision<br/>decided_at"]
      REDEEM["<b>redemptions</b><br/>reward_key · points_spent"]
    end

    subgraph KL["Knowledge layer"]
      direction TB
      subgraph KG["informal_network"]
        direction TB
        NODES["<b>nodes</b><br/>key · type · name"]
        EDGES["<b>edges</b><br/>relation · evidence<br/>confidence"]
      end

      subgraph RAG["rag"]
        direction TB
        DOCS["<b>documents</b><br/>filename"]
        CHUNKS["<b>chunks</b><br/>section · text<br/>embedding vector"]
      end
    end

    subgraph LLM["llm"]
      CALLS["<b>llm_calls</b> ✔ existe<br/>purpose · model<br/>input_tokens · output_tokens<br/>latency_ms"]
    end

    PEOPLE -- "1 : N" --> ASSIGN
    QUESTS -- "1 : N" --> ASSIGN
    ASSIGN -- "1 : N" --> EVID
    ASSIGN -- "1 : 0..1" --> APPR
    PEOPLE -- "1 : N" --> REDEEM
    NODES -- "1 : N origen" --> EDGES
    NODES -- "1 : N destino" --> EDGES
    DOCS -- "1 : N" --> CHUNKS

    PEOPLE <-. "misma key, sin FK" .-> NODES
    DOCS <-. "por key" .-> NODES
  end
  style FONDO fill:#fef9c3,stroke:#fef9c3
  style KL fill:#e0f2fe,stroke:#0369a1,stroke-width:2px
  classDef existe fill:#dcfce7,stroke:#15803d,color:#111827
  class CALLS existe
```

| Tablas | Módulo dueño | Estado |
|---|---|---|
| `llm_calls` | `llm` (Plataforma) | **existe** (migración 0002) |
| `people`, `quests`, `quest_assignments`, `evidence`, `approvals`, `redemptions` | `game` (Experiencia) | diseñadas |
| `nodes`, `edges` | `knowledge.informal_network` (Grafo cultural) | diseñadas |
| `documents`, `chunks` | `knowledge.rag` (RAG) | diseñadas; la dimensión del vector espera el ADR 0005 |

**No hay claves foráneas entre módulos.** Una persona de `game` y su nodo en la
red informal se relacionan por la misma `key`, no por FK; lo mismo un documento
con el tema o proceso que describe. Así cada módulo migra
sus tablas sin depender de otro, y cambiar el motor de uno (por ejemplo, el grafo
a Neo4j) no arrastra a los demás.

---

## 6. Ejecución y camino a producción

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#fef9c3",
    "primaryColor": "#ffffff",
    "primaryTextColor": "#111827",
    "primaryBorderColor": "#374151",
    "secondaryColor": "#fde68a",
    "tertiaryColor": "#fffbeb",
    "lineColor": "#111827",
    "textColor": "#111827",
    "clusterBkg": "#fef3c7",
    "clusterBorder": "#b45309",
    "edgeLabelBackground": "#fef9c3",
    "noteBkgColor": "#fde68a",
    "noteTextColor": "#111827",
    "actorBkg": "#ffffff",
    "actorBorder": "#374151",
    "actorTextColor": "#111827",
    "actorLineColor": "#374151",
    "signalColor": "#111827",
    "signalTextColor": "#111827",
    "labelBoxBkgColor": "#ffffff",
    "labelTextColor": "#111827",
    "loopTextColor": "#111827"
  }
}}%%
flowchart LR
  %% Recuadro amarillo: fondo fijo, igual en editores claros y oscuros
  subgraph FONDO[" "]
    direction LR
    subgraph LOCAL["Local: cada integrante"]
      SRC["src/ en tu disco<br/>código + *_test.py"]
      APPD["app (dev)<br/>hot reload"]
      DBD[("db<br/>pgvector")]
      TUN["tunnel<br/>cloudflared"]
      SRC -. volumen .-> APPD
      APPD --> DBD
      TUN --> APPD
    end

    subgraph GH["GitHub"]
      PR["Pull Request"]
      CI{"CI<br/>lint · tests · migraciones · build"}
      MAIN["main"]
      PR --> CI
      CI -- "verde + review del dueño" --> MAIN
    end

    subgraph PROD["Producción"]
      RENDER["Render<br/>app (prod) sin tests"]
      NEON[("Neon<br/>pgvector")]
      RENDER --> NEON
    end

    SLACK["Slack"]
    OR["OpenRouter"]

    SRC -- "git push" --> PR
    MAIN -- "auto-deploy<br/>alembic upgrade head" --> RENDER
    SLACK -- "dev: app de prueba" --> TUN
    SLACK -- "demo" --> RENDER
    RENDER --> OR
    APPD -. "LLM_PROVIDER" .-> OR
  end
  style FONDO fill:#fef9c3,stroke:#fef9c3
```

En desarrollo y en CI el modelo por defecto es `fake`: no hay llamadas a
OpenRouter hasta que alguien lo configure en su `.env`.

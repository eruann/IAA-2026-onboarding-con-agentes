# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

import sys
import tomllib
from pathlib import Path

import streamlit as st
from pydantic import SecretStr

# streamlit run solo agrega la carpeta de este archivo al path: sumamos src/ para
# poder importar el paquete onboarding del proyecto (todavía no se puede usar
# onboarding.paths, que es justamente lo que se quiere importar)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from onboarding.agents.extract_knowledge import extract_triples  # noqa: E402
from onboarding.config import get_settings  # noqa: E402
from onboarding.knowledge import load_graph, save_triples  # noqa: E402
from onboarding.llm import get_chat_model, load_prompt, model_catalog  # noqa: E402
from onboarding.paths import CORPUS_DIR  # noqa: E402

CONFIRMED = 1  # estado de una relación confirmada en el grafo (store.py)

# Modelos de Claude para la extracción (pagos, por API)
MODELOS_CLAUDE = ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]

# Claude: la clave se lee de secrets.toml, al lado de este archivo (ANTHROPIC_API_KEY).
# Así funciona desde cualquier carpeta y en la máquina de cualquiera.
with open(Path(__file__).with_name("secrets.toml"), "rb") as f:
    CLAVE_ANTHROPIC = tomllib.load(f)["ANTHROPIC_API_KEY"]

# La configuración del proyecto (.env), con dos cambios para esta app: la clave de
# Claude de secrets.toml y Ollama en esta máquina (la app no corre en Docker, así
# que no llega a http://ollama:11434). El contexto de Ollama se fija al arrancarlo:
# OLLAMA_CONTEXT_LENGTH=16384 (ver docs/setup.md).
AJUSTES = get_settings().model_copy(
    update={
        "anthropic_api_key": SecretStr(CLAVE_ANTHROPIC),
        "openai_compat_base_url": "http://localhost:11434/v1",
    }
)


def modelos_extraccion():
    """Claude más los modelos que haya instalados en Ollama (los mismos que lista el
    selector de los talleres). Si Ollama está cerrado, solo Claude."""
    locales = [o.model for o in model_catalog(AJUSTES).options if o.provider == "openai_compat"]
    return MODELOS_CLAUDE + locales


def crear_modelo(nombre):
    # Siempre desde onboarding.llm (regla 5): acá solo se elige el proveedor
    if nombre.startswith("claude"):
        return get_chat_model(AJUSTES, provider="anthropic", model=nombre, max_tokens=2048)
    return get_chat_model(AJUSTES, provider="openai_compat", model=nombre)


@st.cache_data  # se lee una sola vez, no en cada recarga de la página
def leer_md(ruta):
    """Lee el .md tal cual: ya está en Markdown, no hay nada que convertir."""
    return Path(ruta).read_text(encoding="utf-8")


procedimiento = leer_md(CORPUS_DIR / "tesoreria.md")
organigrama = leer_md(CORPUS_DIR / "organigrama.md")

# Modelos disponibles en el selector: nombre visible -> id del modelo
MODELOS = {
    "Gemma 3 4B (local, gratis)": "gemma3:4b",
    "Claude Opus 5.5 (API, pago)": "claude-opus-5-5",
}

# Instrucciones para el modelo (prompt.md, al lado: regla 6), con el organigrama y
# el procedimiento como contexto
instrucciones = (
    f"{load_prompt(Path(__file__).with_name('prompt.md'))}\n"
    f"<organigrama>\n{organigrama}\n</organigrama>\n\n"
    f"<procedimiento_tesoreria>\n{procedimiento}\n</procedimiento_tesoreria>\n"
)

st.title("On Boarding")

# Inicio de sesión: pedir el nombre antes de mostrar el chat
if "nombre" not in st.session_state:
    with st.form("login"):
        nombre = st.text_input("¿Cómo te llamás?")
        if st.form_submit_button("Comenzar") and nombre.strip():
            st.session_state.nombre = nombre.strip()
            st.session_state.system = (
                f"{instrucciones}\nEl usuario se llama {st.session_state.nombre}. "
                "Llamalo por su nombre."
            )
            st.session_state.messages = []
            st.rerun()
    st.stop()

# Barra lateral con el usuario y el botón para cerrar sesión
with st.sidebar:
    st.write(f"Sesión de **{st.session_state.nombre}**")
    modelo = MODELOS[st.selectbox("Modelo", MODELOS, key="modelo")]
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

st.write(
    f"Hola {st.session_state.nombre}, preguntame quién es quién en la empresa "
    "o cómo funciona Tesorería."
)

# Prueba de extract_triples: texto libre -> relaciones para la red informal
with st.expander("Probar extracción de relaciones"):
    texto = st.text_area(
        "Texto",
        placeholder="Pegá una conversación. Ej.: A Julián Rearte me lo presentó Ignacio Pereyra.",
    )
    modelo_extraccion = st.selectbox(
        "Modelo para extraer",
        modelos_extraccion(),
        key="modelo_extraccion",
        help="Claude es pago y corre por API. Los demás son los instalados en Ollama.",
    )
    if st.button("Extraer") and texto.strip():
        try:
            with st.spinner(f"Extrayendo con {modelo_extraccion}..."):
                triples = extract_triples(texto, crear_modelo(modelo_extraccion))
        except Exception as e:  # modelo sin memoria suficiente, sin salida estructurada, etc.
            st.error(f"{modelo_extraccion} falló: {e}")
            st.stop()
        if triples:
            orden = {"high": 0, "medium": 1, "low": 2}  # lo más crítico arriba
            triples = sorted(triples, key=lambda t: orden[t.criticality])
            reporte = save_triples(triples)
            estados = {0: "pendiente", CONFIRMED: "confirmado", None: "no guardada"}
            # vars: la dataclass como dict, más el estado con que quedó en el grafo
            st.table(
                [
                    {**vars(t), "estado": estados[s]}
                    for t, s in zip(triples, reporte.statuses, strict=True)
                ]
            )
            st.success(f"En el grafo: {reporte.summary()}.")
        else:
            st.info("No se encontraron relaciones con respaldo textual.")

# Lo guardado en data/informal_network.json, para revisar estados y conflictos
with st.expander("Grafo guardado"):
    grafo = load_graph()
    if not grafo["edges"]:
        st.info("Todavía no hay relaciones guardadas.")
    else:
        nombres = {n["id"]: n["name"] for n in grafo["nodes"]}
        st.table(
            [
                {
                    "estado": "confirmado" if e["status"] == CONFIRMED else "pendiente",
                    "sujeto": nombres[e["source"]],
                    "relación": e["relation"],
                    "objeto": nombres[e["target"]],
                    "criticidad": e.get("criticality", ""),
                    "frase": e["evidence"],
                    "cambios": " | ".join(h["evidence"] for h in e["history"]),
                }
                for e in grafo["edges"]
            ]
        )
        conflictos = [n for n in grafo["nodes"] if n["type"] == "conflict"]
        for c in conflictos:
            frases = " vs. ".join(f"«{f}»" for f in c["attributes"]["evidence"])
            st.warning(f"{c['name']}: {frases}")

# Mostrar el historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def responder():
    """La respuesta en partes, con el mismo código para Claude y para Ollama."""
    chat = crear_modelo(modelo)
    mensajes = [{"role": "system", "content": st.session_state.system}]
    for chunk in chat.stream(mensajes + st.session_state.messages):
        # Claude con razonamiento manda bloques (thinking + texto): solo se muestra el texto
        if isinstance(chunk.content, str):
            yield chunk.content
        else:
            yield "".join(
                b.get("text", "")
                for b in chunk.content
                if isinstance(b, dict) and b.get("type") == "text"
            )


def explicar(error):
    """El error en castellano. Se reconoce por el nombre de la clase, como en
    ui/errors.py: así no hace falta importar el SDK de cada proveedor."""
    # LangChain a veces les antepone el proveedor (OpenAIAuthenticationError)
    nombre = type(error).__name__.removeprefix("OpenAI")
    if nombre == "AuthenticationError":
        return "La clave no es válida. Revisá ANTHROPIC_API_KEY en secrets.toml."
    if nombre in {"APIConnectionError", "ConnectError", "ConnectionError"}:
        return (
            "No se pudo conectar con el modelo. "
            "Si es Ollama, ¿está abierto? Probá con `ollama serve`."
        )
    return f"Error del modelo ({nombre}): {error}"


pregunta = st.chat_input("Escribe tu pregunta aquí...")
if pregunta:
    with st.chat_message("user"):
        st.markdown(pregunta)
    st.session_state.messages.append({"role": "user", "content": pregunta})

    with st.chat_message("assistant"):
        try:
            respuesta = st.write_stream(responder())
        except Exception as e:  # sin conexión, clave inválida, error del proveedor
            st.session_state.messages.pop()  # la pregunta falló: no la dejamos en el historial
            st.error(explicar(e))
            st.stop()
    st.session_state.messages.append({"role": "assistant", "content": respuesta})

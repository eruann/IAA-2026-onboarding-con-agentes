import sys
import tomllib
from pathlib import Path

import anthropic
import ollama
import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

# Carpeta corpus/ del repo, buscada desde este archivo: funciona desde cualquier carpeta
CORPUS = Path(__file__).resolve().parents[3] / "corpus"

# streamlit run solo agrega la carpeta de este archivo al path: sumamos src/ para
# poder importar el paquete onboarding del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from onboarding.knowledge.informal_network.extraction import extract_triples  # noqa: E402

# Modelos de Claude para la extracción (pagos, por API)
MODELOS_CLAUDE = ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]


def modelos_extraccion():
    """Claude más los modelos que haya instalados en Ollama, leídos en cada recarga."""
    try:
        locales = [m.model for m in ollama.list().models]
    except Exception:  # Ollama cerrado: solo se ofrece Claude
        locales = []
    return MODELOS_CLAUDE + locales


def crear_modelo(nombre):
    if nombre.startswith("claude"):
        # Claude 5 no acepta temperature
        return ChatAnthropic(model=nombre, api_key=CLAVE_ANTHROPIC, max_tokens=2048)
    return ChatOllama(model=nombre, temperature=0.0, num_ctx=8192)


@st.cache_data  # se lee una sola vez, no en cada recarga de la página
def leer_md(ruta):
    """Lee el .md tal cual: ya está en Markdown, no hay nada que convertir."""
    return Path(ruta).read_text(encoding="utf-8")


procedimiento = leer_md(CORPUS / "tesoreria.md")
organigrama = leer_md(CORPUS / "organigrama.md")

# Claude: la clave se lee de C:\Cursos\lang_chain\.streamlit\secrets.toml (ANTHROPIC_API_KEY).
# Se busca por la ubicación de este archivo, así funciona desde cualquier carpeta.
SECRETS = r"C:\IAA\repo\IAA-2026-onboarding-con-agentes\src\onboarding\mi_caperta\secrets.toml"
with open(SECRETS, "rb") as f:
    CLAVE_ANTHROPIC = tomllib.load(f)["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=CLAVE_ANTHROPIC)

# Modelos disponibles en el selector: nombre visible -> id del modelo
MODELOS = {
    "Gemma 3 4B (local, gratis)": "gemma3:4b",
    "Claude Opus 5.5 (API, pago)": "claude-opus-5-5",
}

# Instrucciones para el modelo, con el organigrama y el procedimiento como contexto
instrucciones = f"""Sos un asistente de onboarding para empleados nuevos de Farmalog Sur.
Respondé siempre en español, de forma breve y amable.
Usá solo la información del organigrama y del procedimiento de Tesorería. Si no sabés algo, decilo.
Cuando respondas sobre el procedimiento, indicá la sección de donde sale la información.

<organigrama>
{organigrama}
</organigrama>

<procedimiento_tesoreria>
{procedimiento}
</procedimiento_tesoreria>
"""

st.title("On Boarding")

# Inicio de sesión: pedir el nombre antes de mostrar el chat
if "nombre" not in st.session_state:
    with st.form("login"):
        nombre = st.text_input("¿Cómo te llamás?")
        if st.form_submit_button("Comenzar") and nombre.strip():
            st.session_state.nombre = nombre.strip()
            # El bloque grande se cachea; el nombre va aparte para no romper el caché entre usuarios
            st.session_state.system = [
                {"type": "text", "text": instrucciones, "cache_control": {"type": "ephemeral"}},
                {
                    "type": "text",
                    "text": f"El usuario se llama {st.session_state.nombre}. "
                    "Llamalo por su nombre.",
                },
            ]
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
            st.table([vars(t) for t in triples])  # vars: la dataclass como dict
        else:
            st.info("No se encontraron relaciones con respaldo textual.")

# Mostrar el historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def responder_ollama():
    # Ollama recibe las instrucciones como un mensaje de sistema más
    system = "\n\n".join(bloque["text"] for bloque in st.session_state.system)
    # num_ctx: el procedimiento no entra en la ventana por defecto de Ollama (2048 tokens)
    chat = ChatOllama(model=modelo, temperature=0.0, num_ctx=16384)
    for chunk in chat.stream([{"role": "system", "content": system}] + st.session_state.messages):
        yield chunk.content


def responder_claude():
    # Si Claude rechaza la consulta, la API la reintenta con otro modelo (fallbacks)
    with client.beta.messages.stream(
        model=modelo,
        max_tokens=16000,
        system=st.session_state.system,
        messages=st.session_state.messages,
        output_config={"effort": "low"},  # chat simple: respuestas rápidas
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        yield from stream.text_stream


pregunta = st.chat_input("Escribe tu pregunta aquí...")
if pregunta:
    with st.chat_message("user"):
        st.markdown(pregunta)
    st.session_state.messages.append({"role": "user", "content": pregunta})

    with st.chat_message("assistant"):
        try:
            if modelo.startswith("claude"):
                respuesta = st.write_stream(responder_claude())
            else:
                respuesta = st.write_stream(responder_ollama())
        except ConnectionError:
            st.session_state.messages.pop()
            st.error("No se pudo conectar con Ollama. ¿Está abierto? Probá con `ollama serve`.")
            st.stop()
        except anthropic.AuthenticationError:
            st.session_state.messages.pop()  # la pregunta falló: no la dejamos en el historial
            st.error("La clave ANTHROPIC_API_KEY no es válida.")
            st.stop()
        except anthropic.APIError as e:
            st.session_state.messages.pop()
            st.error(f"Error de la API de Claude: {e}")
            st.stop()
    st.session_state.messages.append({"role": "assistant", "content": respuesta})

# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""El agente que responde las preguntas del ingresante. Titular: rol RAG y evaluación."""

from pathlib import Path

from langchain_core.language_models import BaseChatModel

from onboarding.agents.common import Node, NodeSpec, ask_model
from onboarding.agents.state import OnboardingState
from onboarding.knowledge import RetrievedChunk, retrieve, who_knows_about

PROMPT = Path(__file__).with_name("prompt.md")


def _context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return (
            "<fragmentos>\n"
            "(no se encontró documentación relacionada con la pregunta)\n"
            "</fragmentos>"
        )
    fragments = "\n\n".join(
        f'<fragmento documento="{chunk.document}" seccion="{chunk.section}">\n'
        f"{chunk.text}\n</fragmento>"
        for chunk in chunks
    )
    return f"<fragmentos>\n{fragments}\n</fragmentos>"


# recorrido: nodo-respuesta
def make_answer_question(model: BaseChatModel) -> Node:
    def answer_question(state: OnboardingState) -> dict:
        chunks = retrieve(state.get("input", ""), k=5)
        output = ask_model(model, PROMPT, state, _context(chunks))
        citations = list(dict.fromkeys(f"{chunk.document} § {chunk.section}" for chunk in chunks))

        referred_to = None
        if not chunks:
            # Sin ningún fragmento (corpus vacío, por ejemplo): no hay nada para
            # ofrecerle al modelo, así que conviene derivar directo.
            # TODO(rag): esto no cubre "hubo fragmentos pero ninguno sirve" — se
            # midió que el score de similitud de este modelo no separa bien esos
            # casos de los respondibles (ver ADR 0005). Mientras tanto, esa parte
            # queda en manos del prompt: le pide al modelo decir que no sabe y
            # derivar en el texto de la respuesta, sin estructurar a quién acá.
            try:
                people = who_knows_about(state.get("input", ""))
            except NotImplementedError:
                people = []
            referred_to = people[0] if people else None

        return {"output": output, "citations": citations, "referred_to": referred_to}

    return answer_question


NODE = NodeSpec(
    "answer_question", "Responder pregunta", "RAG y evaluación", make_answer_question, PROMPT
)

# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Agente que responde preguntas con la knowledge layer. Titular: rol RAG y evaluación."""

from onboarding.agents.answer_question.node import NODE, make_answer_question

__all__ = ["NODE", "make_answer_question"]

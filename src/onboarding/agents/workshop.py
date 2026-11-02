"""Talleres del módulo agents: el del coordinador y el del rol Agentes."""

from pathlib import Path

from onboarding.agents.prompts import load_prompt
from onboarding.workshop import Tool, Workshop


def show_prompt(name: str) -> str:
    """El prompt de un agente tal como lo recibe el modelo (agents/prompts/<name>.md)."""
    return load_prompt(name)


# recorrido: taller-agentes
WORKSHOPS = (
    Workshop(
        key="agentes",
        role="Agentes y orquestación",
        agent="generate_quest",
        summary=(
            "El Diseñador de misiones, las tools que usan los agentes, el versionado "
            "de prompts y la comparación de modelos por costo y latencia."
        ),
        tools=(Tool(show_prompt, "Ver un prompt", "Ej.: generate_quest, answer_question, quests"),),
        guide=Path(__file__).parent / "LEEME.md",
    ),
    Workshop(
        key="coordinador",
        role="Tech Lead",
        agent=None,
        summary=(
            "El coordinador: sin agente elegido, decide a quién va cada mensaje. "
            "Acá el chat no fuerza agente, así se ve qué elige."
        ),
        guide=Path(__file__).parent / "coordinator" / "LEEME.md",
    ),
)

"""Taller del rol Experiencia: el agente Mis misiones y las reglas del juego."""

from pathlib import Path

from onboarding.game.points import level_for
from onboarding.workshop import Tool, Workshop

# recorrido: taller-experiencia
WORKSHOP = Workshop(
    key="experiencia",
    role="Experiencia",
    agent="quests",
    summary=(
        "Lo que la gente ve y toca: el juego (misiones, puntos, canje), el panel del "
        "jefe y el agente que acompaña al ingresante en sus misiones."
    ),
    tools=(Tool(level_for, "Nivel según puntos", "Cuántos puntos hacen falta para cada nivel."),),
    guide=Path(__file__).parent / "LEEME.md",
)

# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Dial de tono: de checklist seria a mapa con avatares.

Cada empresa elige dónde pararse. El tono cambia los textos, nunca las reglas
del juego ni los permisos.
"""

from enum import StrEnum


class Tone(StrEnum):
    SERIOUS = "serious"  # checklist con reconocimiento
    BALANCED = "balanced"  # misiones con puntos, sin avatares
    PLAYFUL = "playful"  # mapa, niveles, avatares


DEFAULT_TONE = Tone.BALANCED

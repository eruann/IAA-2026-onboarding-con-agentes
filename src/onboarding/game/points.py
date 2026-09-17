"""Puntos y niveles.

Criterio del TP (sale de la evidencia sobre gamificación, ver la propuesta):
se dan puntos por aprender y por recorrer la organización, no por rendimiento, y
el ranking es opcional. Mal aplicado, esto erosiona la autonomía en vez de
ayudar.
"""

LEVELS = [(0, "Recién llegado"), (100, "En marcha"), (250, "Con calle"), (500, "Referente")]


def level_for(points: int) -> str:
    if points < 0:
        raise ValueError("los puntos no pueden ser negativos")
    name = LEVELS[0][1]
    for threshold, level_name in LEVELS:
        if points >= threshold:
            name = level_name
    return name

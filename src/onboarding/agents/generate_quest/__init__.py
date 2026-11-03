# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Diseñador de misiones: propone misiones nuevas. Titular: rol Diseñador de misiones."""

from onboarding.agents.generate_quest.node import NODE, make_generate_quest
from onboarding.agents.generate_quest.workshop import WORKSHOP

__all__ = ["NODE", "WORKSHOP", "make_generate_quest"]

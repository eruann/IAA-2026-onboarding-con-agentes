# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""El agente que revisa la evidencia de una misión. Titular: rol Experiencia."""

from pathlib import Path

from onboarding.agents.common import Models, Node, NodeSpec, ask_model
from onboarding.agents.state import OnboardingState

PROMPT = Path(__file__).with_name("prompt.md")


# recorrido: nodo-evidencia
def make_validate_evidence(models: Models) -> Node:
    def validate_evidence(state: OnboardingState) -> dict:
        # TODO(experiencia): decidir aprobada / rechazada / requiere revisión humana.
        # La aprobación final del jefe siempre gana sobre el agente.
        return {"output": ask_model(models.main, PROMPT, state)}

    return validate_evidence


NODE = NodeSpec(
    "validate_evidence", "Validar evidencia", "Experiencia", make_validate_evidence, PROMPT
)

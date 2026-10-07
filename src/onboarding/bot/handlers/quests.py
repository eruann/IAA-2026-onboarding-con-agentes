"""Comandos de misiones: ver las propias, entregar evidencia."""

from pathlib import Path

import yaml
from slack_bolt import App

QUESTS_FILE = Path("data/quests.yaml")


def register(app: App) -> None:
    @app.command("/misiones-fausto")
    @app.command("/misiones")
    def list_quests(ack, respond, command):
        # ack() primero y siempre: Slack corta a los 3 segundos.
        ack()
        quests = yaml.safe_load(QUESTS_FILE.read_text(encoding="utf-8")) or []
        if not quests:
            respond("Todavía no hay misiones cargadas.", response_type="ephemeral")
            return

        lines = ["*Misiones de onboarding*\n"]
        for quest in quests:
            lines.extend(
                [
                    f"*{quest['title']}* · {quest['points']} puntos",
                    quest["description"],
                    f"_Evidencia:_ {quest['evidence_required']}",
                    "",
                ]
            )
        respond("\n".join(lines), response_type="ephemeral")

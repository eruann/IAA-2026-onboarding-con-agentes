"""Tablas del juego. Titular: rol Experiencia.

TODO(experiencia): definir y migrar

    people(id, slack_user_id, name, role, area, is_newcomer)
    quests(id, key, title, description, points, approver, evidence_required)
    quest_assignments(id, quest_id, person_id, status, assigned_at, completed_at)
    evidence(id, assignment_id, text, url, submitted_at)
    approvals(id, assignment_id, approved_by, decision, decided_at)
    redemptions(id, person_id, reward_key, points_spent, created_at)

`approvals` guarda quién aprobó y cuándo: la métrica del TP es horas-persona de
la organización, y sin ese registro no hay forma de medirla.
"""

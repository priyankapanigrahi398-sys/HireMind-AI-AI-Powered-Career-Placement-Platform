import json
from app.models import UserSkill, EvidenceEvent, TargetRole
from app.services.matcher import canon

# How much each kind of evidence moves the score.
SOURCE_WEIGHT = {"quiz": 0.35, "coding": 0.4, "interview": 0.4}

# A resume claim sets a modest starting point, but never overrides real evidence.
RESUME_START = 0.3


def record_evidence(db, user_id: int, skill: str, source: str, score: float):
    skill = canon(skill)
    score = max(0.0, min(1.0, score))

    row = db.query(UserSkill).filter_by(user_id=user_id, skill=skill).first()
    is_new = row is None
    if is_new:
        row = UserSkill(user_id=user_id, skill=skill, mastery=0.0, confidence=0.0)
        db.add(row)

    if source == "resume":
        if is_new:
            row.mastery = RESUME_START
            row.confidence = 0.1
    else:
        lr = SOURCE_WEIGHT.get(source, 0.2)
        row.mastery = round(row.mastery + lr * (score - row.mastery), 4)
        row.confidence = round(min(1.0, row.confidence + lr * 0.5), 4)

    db.add(EvidenceEvent(user_id=user_id, skill=skill, source=source, score=score))
    db.commit()
    return row


def compute_gaps(db, user_id: int):
    target = (
        db.query(TargetRole)
        .filter_by(user_id=user_id)
        .order_by(TargetRole.id.desc())
        .first()
    )
    if target is None:
        return None

    required = json.loads(target.required_json)
    have = {s.skill: s for s in db.query(UserSkill).filter_by(user_id=user_id)}

    gaps = []
    weighted = 0.0
    total = 0.0
    for item in required:
        name = item.get("name", "")
        importance = float(item.get("importance", 3))
        mastery = have[canon(name)].mastery if canon(name) in have else 0.0
        total += importance
        weighted += importance * mastery
        gaps.append({
            "skill": name,
            "importance": importance,
            "mastery": mastery,
            "priority": round(importance / 5 * (1 - mastery), 3),
        })

    gaps.sort(key=lambda g: -g["priority"])
    readiness = round(100 * weighted / total, 1) if total else 0.0
    return {"role": target.title, "readiness_percentage": readiness, "gaps": gaps}
import json
from app.services.llm import generate_json
from app.services.mastery import compute_gaps
from app.models import RoadmapItem

MAX_ITEMS = 5
MASTERED = 0.75

TITLES = {
    "learn": "Learn the fundamentals of {skill}",
    "practice_quiz": "Practice {skill} with a quiz round",
    "mock_interview": "Do a mock interview round on {skill}",
}


def pick_type(mastery: float, learn_done: bool):
    if mastery >= MASTERED:
        return None
    if mastery < 0.25 and not learn_done:
        return "learn"
    if mastery < 0.5:
        return "practice_quiz"
    return "mock_interview"


def generate_steps(skills: list) -> dict:
    if not skills:
        return {}

    prompt = (
        "You are a placement coach for a college student. For each skill "
        "below, write a short study plan. Return JSON with one key 'plans', "
        "a list of objects with: skill (copied exactly from the list), "
        "steps (list of 3 to 4 short, concrete study steps, ordered from "
        "basics to practice), practice (one small hands-on task, one "
        "sentence).\n\nSkills: " + ", ".join(skills)
    )

    try:
        data = generate_json(prompt, temperature=0.4)
    except Exception:
        return {}

    out = {}
    for plan in data.get("plans", []):
        name = str(plan.get("skill", "")).strip().lower()
        steps = plan.get("steps", [])
        if name and isinstance(steps, list) and steps:
            out[name] = {
                "steps": [str(s) for s in steps][:5],
                "practice": str(plan.get("practice", "")),
            }
    return out


def sync_roadmap(db, user_id: int):
    result = compute_gaps(db, user_id)
    if result is None:
        return None

    items = db.query(RoadmapItem).filter_by(user_id=user_id).all()
    done_learn = {
        i.skill.lower()
        for i in items
        if i.status == "done" and i.task_type == "learn"
    }
    todo = {
        (i.skill.lower(), i.task_type): i
        for i in items
        if i.status == "todo"
    }

    desired = []
    for gap in result["gaps"]:
        task_type = pick_type(gap["mastery"], gap["skill"].lower() in done_learn)
        if task_type:
            desired.append((gap, task_type))
    desired = desired[:MAX_ITEMS]
    desired_keys = {(g["skill"].lower(), t) for g, t in desired}

    for key, item in todo.items():
        if key not in desired_keys:
            item.status = "superseded"

    new_items = [(g, t) for g, t in desired if (g["skill"].lower(), t) not in todo]
    steps = generate_steps([g["skill"] for g, t in new_items if t == "learn"])

    for gap, task_type in new_items:
        skill = gap["skill"]
        if task_type == "learn":
            details = steps.get(skill.lower()) or {
                "steps": [
                    f"Read a beginner tutorial on {skill}",
                    f"Follow along and build a tiny example with {skill}",
                    f"Write down 5 questions an interviewer might ask about {skill}",
                ],
                "practice": f"Build a small project that uses {skill}.",
            }
        elif task_type == "practice_quiz":
            details = {"how": "Take a quiz round to test what you know."}
        else:
            details = {"how": "Answer interview questions out loud, then in writing."}

        db.add(RoadmapItem(
            user_id=user_id,
            skill=skill,
            task_type=task_type,
            title=TITLES[task_type].format(skill=skill),
            details_json=json.dumps(details),
            status="todo",
        ))

    db.commit()
    return result
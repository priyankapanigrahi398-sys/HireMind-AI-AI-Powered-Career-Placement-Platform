import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RoadmapItem
from app.routers.students import get_user_or_404
from app.services.roadmap import sync_roadmap

router = APIRouter(prefix="/users", tags=["roadmap"])

NEXT_ACTION = {
    "learn": "Follow the steps, then mark it done: POST /users/{uid}/roadmap/{iid}/complete",
    "practice_quiz": "Take a quiz: POST /users/{uid}/quiz/generate, then /quiz/submit",
    "mock_interview": "Practice: POST /users/{uid}/interview/start (set skill), then /interview/answer",
}


@router.get("/{user_id}/roadmap")
def get_roadmap(user_id: int, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    result = sync_roadmap(db, user_id)
    if result is None:
        raise HTTPException(400, "Set a target role first (POST /users/{id}/target).")

    gap_by_skill = {g["skill"].lower(): g for g in result["gaps"]}
    items = db.query(RoadmapItem).filter_by(user_id=user_id, status="todo").all()

    plan = []
    for item in items:
        gap = gap_by_skill.get(item.skill.lower(), {})
        plan.append({
            "item_id": item.id,
            "skill": item.skill,
            "task_type": item.task_type,
            "title": item.title,
            "priority": gap.get("priority", 0),
            "current_mastery": gap.get("mastery", 0),
            "details": json.loads(item.details_json or "{}"),
            "next_action": NEXT_ACTION[item.task_type].format(uid=user_id, iid=item.id),
        })

    plan.sort(key=lambda p: -p["priority"])
    for rank, entry in enumerate(plan, start=1):
        entry["rank"] = rank

    done_count = db.query(RoadmapItem).filter_by(user_id=user_id, status="done").count()

    return {
        "role": result["role"],
        "readiness_percentage": result["readiness_percentage"],
        "tasks_completed": done_count,
        "plan": plan,
    }


@router.post("/{user_id}/roadmap/{item_id}/complete")
def complete(user_id: int, item_id: int, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    item = db.get(RoadmapItem, item_id)
    if item is None or item.user_id != user_id:
        raise HTTPException(404, "Roadmap item not found.")
    if item.status != "todo":
        raise HTTPException(400, "This item is not an active task.")

    item.status = "done"
    item.completed_at = datetime.now(timezone.utc)
    db.commit()

    if item.task_type == "learn":
        message = (
            "Nice work. Studying alone does not raise your score. "
            "Prove it with a quiz round next: GET /users/{}/roadmap".format(user_id)
        )
    else:
        message = "Marked done. Your score changes only through quiz, interview, or coding results."

    return {"item_id": item.id, "status": "done", "message": message}
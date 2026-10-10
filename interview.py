from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InterviewQuestion
from app.routers.students import get_user_or_404
from app.services.interview import generate_interview, score_answer
from app.services.mastery import record_evidence

router = APIRouter(prefix="/users", tags=["interview"])


class AnswerIn(BaseModel):
    question_id: int
    answer: str


@router.post("/{user_id}/interview/start")
def start(
    user_id: int,
    kind: str = "technical",
    n: int = 3,
    skill: Optional[str] = None,
    db: Session = Depends(get_db),
):
    get_user_or_404(db, user_id)
    if kind not in ("technical", "hr"):
        raise HTTPException(400, "kind must be 'technical' or 'hr'.")
    n = max(2, min(n, 8))

    questions = generate_interview(db, user_id, kind, n, skill)
    if questions is None:
        raise HTTPException(400, "Set a target role first (POST /users/{id}/target).")
    if not questions:
        raise HTTPException(502, "The AI returned no valid questions. Try again.")

    return [
        {"question_id": q.id, "skill": q.skill, "question": q.question}
        for q in questions
    ]


@router.post("/{user_id}/interview/answer")
def answer(user_id: int, body: AnswerIn, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    q = db.get(InterviewQuestion, body.question_id)
    if q is None or q.user_id != user_id:
        raise HTTPException(404, "Question not found.")
    if q.answered:
        raise HTTPException(400, "This question was already answered.")

    text = body.answer.strip()
    if len(text) < 10:
        raise HTTPException(400, "Please write a longer answer (at least 10 characters).")
    text = text[:3000]

    result = score_answer(q.question, q.skill, text, q.kind)

    q.answered = 1
    q.answer_text = text
    q.correctness = result["correctness"]
    q.depth = result["depth"]
    q.clarity = result["clarity"]
    q.structure = result["structure"]
    q.overall = result["overall"]
    q.feedback = result["feedback"]
    db.commit()

    new_mastery = None
    if q.skill:
        row = record_evidence(db, user_id, q.skill, "interview", result["overall"])
        new_mastery = row.mastery

    return {
        "question_id": q.id,
        "skill": q.skill,
        "scores": {
            "correctness": result["correctness"],
            "depth": result["depth"],
            "clarity": result["clarity"],
            "structure": result["structure"],
        },
        "overall_out_of_100": round(result["overall"] * 100),
        "skill_mastery_now": new_mastery,
        "feedback": result["feedback"],
        "tips": result["tips"],
    }


@router.get("/{user_id}/interview/summary")
def summary(user_id: int, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    rows = (
        db.query(InterviewQuestion)
        .filter_by(user_id=user_id, answered=1)
        .order_by(InterviewQuestion.id.desc())
        .all()
    )
    if not rows:
        return {"answered": 0, "message": "No interview answers yet."}

    def avg(values):
        return round(sum(values) / len(values), 2)

    return {
        "answered": len(rows),
        "average_scores_out_of_5": {
            "correctness": avg([r.correctness for r in rows]),
            "depth": avg([r.depth for r in rows]),
            "clarity": avg([r.clarity for r in rows]),
            "structure": avg([r.structure for r in rows]),
        },
        "average_overall_out_of_100": round(100 * avg([r.overall for r in rows])),
        "recent": [
            {
                "question": r.question,
                "skill": r.skill,
                "overall_out_of_100": round(r.overall * 100),
                "feedback": r.feedback,
            }
            for r in rows[:5]
        ],
    }
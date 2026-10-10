import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import QuizQuestion
from app.routers.students import get_user_or_404
from app.services.quiz import generate_questions
from app.services.mastery import record_evidence, compute_gaps

router = APIRouter(prefix="/users", tags=["quiz"])


class Answer(BaseModel):
    question_id: int
    choice: int  # 0 to 3


class SubmitIn(BaseModel):
    answers: List[Answer]


@router.post("/{user_id}/quiz/generate")
def generate(user_id: int, n: int = 10, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    n = max(3, min(n, 15))
    questions = generate_questions(db, user_id, n)
    if questions is None:
        raise HTTPException(400, "Set a target role first (POST /users/{id}/target).")
    if not questions:
        raise HTTPException(502, "The AI returned no valid questions. Try again.")
    return [
        {
            "question_id": q.id,
            "skill": q.skill,
            "question": q.question,
            "options": json.loads(q.options_json),
        }
        for q in questions
    ]


@router.post("/{user_id}/quiz/submit")
def submit(user_id: int, body: SubmitIn, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    results = []
    correct = 0

    for a in body.answers:
        q = db.get(QuizQuestion, a.question_id)
        if q is None or q.user_id != user_id or q.answered:
            continue
        is_correct = a.choice == q.correct_index
        record_evidence(db, user_id, q.skill, "quiz", 1.0 if is_correct else 0.0)
        q.answered = 1
        db.commit()
        if is_correct:
            correct += 1
        results.append({
            "question_id": q.id,
            "skill": q.skill,
            "correct": is_correct,
            "right_answer": json.loads(q.options_json)[q.correct_index],
            "explanation": q.explanation,
        })

    if not results:
        raise HTTPException(400, "No unanswered questions matched. Generate a new quiz.")

    return {
        "score": f"{correct}/{len(results)}",
        "results": results,
        "updated_gaps": compute_gaps(db, user_id),
    }
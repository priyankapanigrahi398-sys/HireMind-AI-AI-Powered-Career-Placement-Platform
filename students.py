import json
from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserSkill, EvidenceEvent, TargetRole
from app.services.extractor import read_pdf_text, parse_resume_text, parse_jd_text
from app.services.mastery import record_evidence, compute_gaps

router = APIRouter(prefix="/users", tags=["students"])


class UserIn(BaseModel):
    name: str


class EvidenceIn(BaseModel):
    skill: str
    source: str  # resume, quiz, coding, interview
    score: float  # 0 to 1


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    return user


@router.post("")
def create_user(body: UserIn, db: Session = Depends(get_db)):
    user = User(name=body.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name}


@router.post("/{user_id}/resume")
async def upload_resume(user_id: int, file: UploadFile, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    text = read_pdf_text(file.file)
    if not text.strip():
        raise HTTPException(400, "Could not read text from this PDF.")
    parsed = parse_resume_text(text)
    skills = parsed.get("skills", [])
    for s in skills:
        record_evidence(db, user_id, s, "resume", 0.5)
    return {"skills_added": skills}


@router.post("/{user_id}/target")
def set_target(user_id: int, jd_text: str = Form(...), db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    job = parse_jd_text(jd_text)
    db.add(TargetRole(
        user_id=user_id,
        title=job.get("role_title", "Target role"),
        required_json=json.dumps(job.get("required_skills", [])),
    ))
    db.commit()
    return {"role_title": job.get("role_title"), "required_skills": job.get("required_skills", [])}


@router.post("/{user_id}/evidence")
def add_evidence(user_id: int, body: EvidenceIn, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    row = record_evidence(db, user_id, body.skill, body.source, body.score)
    return {"skill": row.skill, "mastery": row.mastery, "confidence": row.confidence}


@router.get("/{user_id}/skills")
def list_skills(user_id: int, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    rows = db.query(UserSkill).filter_by(user_id=user_id).order_by(UserSkill.mastery.desc())
    return [{"skill": r.skill, "mastery": r.mastery, "confidence": r.confidence} for r in rows]


@router.get("/{user_id}/history")
def history(user_id: int, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    rows = db.query(EvidenceEvent).filter_by(user_id=user_id).order_by(EvidenceEvent.id.desc()).limit(50)
    return [{"skill": r.skill, "source": r.source, "score": r.score, "at": r.created_at} for r in rows]


@router.get("/{user_id}/gaps")
def gaps(user_id: int, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    result = compute_gaps(db, user_id)
    if result is None:
        raise HTTPException(400, "Set a target role first (POST /users/{id}/target).")
    return result
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database import Base, engine
from app import models  # noqa: F401
from app.routers import students, quiz, interview, roadmap, auth
from app.services.extractor import read_pdf_text, parse_resume_text, parse_jd_text
from app.services.matcher import compute_match

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HireMind AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(quiz.router)
app.include_router(interview.router)
app.include_router(roadmap.router)


class JobText(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/resume/parse")
async def parse_resume(file: UploadFile):
    text = read_pdf_text(file.file)
    if not text.strip():
        raise HTTPException(400, "Could not read text from this PDF.")
    return parse_resume_text(text)


@app.post("/jobs/parse")
def parse_job(job: JobText):
    return parse_jd_text(job.text)


@app.post("/match")
async def match(file: UploadFile, jd_text: str = Form(...)):
    resume_text = read_pdf_text(file.file)
    if not resume_text.strip():
        raise HTTPException(400, "Could not read text from this PDF.")

    resume = parse_resume_text(resume_text)
    job = parse_jd_text(jd_text)
    result = compute_match(resume.get("skills", []), job.get("required_skills", []))

    return {
        "role_title": job.get("role_title"),
        **result,
        "nice_to_have": job.get("nice_to_have", []),
        "resume_skills": resume.get("skills", []),
    }
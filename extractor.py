from pypdf import PdfReader
from app.services.llm import generate_json


def read_pdf_text(file_obj) -> str:
    reader = PdfReader(file_obj)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_resume_text(text: str) -> dict:
    prompt = (
        "Extract from this resume. Return JSON with keys: "
        "skills (list of technical skills only, short standard names), "
        "education (list), "
        "projects (list of objects with name, tech, summary), "
        "experience (list).\n\nResume:\n" + text
    )
    return generate_json(prompt)


def parse_jd_text(text: str) -> dict:
    prompt = (
        "Extract the requirements from this job description. Return JSON with keys: "
        "role_title (string), "
        "required_skills (list of objects with name and importance, where "
        "importance is a number from 1 to 5 and 5 means essential), "
        "nice_to_have (list of strings). "
        "Use short standard skill names such as Python, SQL, REST APIs, Docker.\n\n"
        "Job description:\n" + text
    )
    return generate_json(prompt)
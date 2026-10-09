# HireMind AI – AI-Powered Career Placement Platform

HireMind AI helps students prepare for jobs. It reads a resume, compares it with a job description, finds skill gaps, and then helps close them with quizzes, mock interviews, and a personalised learning roadmap. The AI features are powered by Google Gemini.

## Features
- **User accounts:** register and log in
- **Resume parsing:** upload a PDF resume and extract skills and details
- **Job description parsing:** extract required skills from any job posting
- **Resume–job matching:** compute how well a resume matches a job
- **Skill gap analysis:** see which skills are missing for a target role
- **AI quizzes:** generate and submit quizzes to test skills
- **AI mock interview:** answer interview questions and get a summary
- **Learning roadmap:** personalised steps that can be marked complete
- **Skill mastery tracking:** progress history across quizzes and interviews

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19 |
| Backend | Python, FastAPI, Uvicorn |
| Database | SQLite with SQLAlchemy |
| AI | Google Gemini (`google-genai`) |
| PDF reading | pypdf |

## Project Structure
```
hiremind/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app and core endpoints
│   │   ├── models.py        # Database models
│   │   ├── database.py      # SQLite connection
│   │   ├── routers/         # auth, students, quiz, interview, roadmap
│   │   └── services/        # extractor, matcher, llm, quiz, interview, roadmap, mastery
│   └── requirements.txt
└── frontend/
    ├── app/                 # Next.js pages and components
    └── package.json
```

## Setup

### Prerequisites
- Python 3.10 or newer
- Node.js 18 or newer
- A Google Gemini API key (get one at https://aistudio.google.com/apikey)

### 1. Clone the repository
```bash
git clone https://github.com/priyankapanigrahi398-sys/hiremind.git
cd hiremind
```

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

Create a file named `.env` inside the `backend` folder:
```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Start the server:
```bash
uvicorn app.main:app --reload
```
The API runs at http://localhost:8000 and the interactive docs are at http://localhost:8000/docs.

### 3. Frontend
Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```
The app runs at http://localhost:3000.

## API Overview
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/auth/register`, `/auth/login` | Create account and log in |
| POST | `/resume/parse` | Parse a PDF resume |
| POST | `/jobs/parse` | Parse a job description |
| POST | `/match` | Match a resume against a job description |
| POST | `/users/{id}/resume` | Save a user's resume |
| POST | `/users/{id}/target` | Set the target job |
| GET | `/users/{id}/skills`, `/gaps`, `/history` | Skills, skill gaps, progress history |
| POST | `/users/{id}/quiz/generate`, `/quiz/submit` | Generate and submit a quiz |
| POST | `/users/{id}/interview/start`, `/interview/answer` | Mock interview |
| GET | `/users/{id}/interview/summary` | Interview summary |
| GET | `/users/{id}/roadmap` | Learning roadmap |
| POST | `/users/{id}/roadmap/{item_id}/complete` | Mark a roadmap item complete |

## Notes
- The `.env` file and the `hiremind.db` database are not included in the repository. Create your own `.env` as shown above, and the database is created automatically on first run.
- Never commit your API key.

## Author
Priyanka Panigrahi

# AI Lens Backend

Python backend for the AI Lens frontend using FastAPI and Gemini API.

## 1) Setup

```bash
cd ai-report-backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Environment

Copy `.env.example` to `.env` and set values:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
PORT=8000
ALLOWED_ORIGIN=http://localhost:5173
```

If no `GEMINI_API_KEY` is set, the backend still works with safe fallback output.

## 3) Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 4) Endpoints

- `GET /health`
- `POST /reports/generate`
- `GET /reports/history`
- `POST /agent/chat`

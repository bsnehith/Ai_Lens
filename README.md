# AI Lens Project

AI Lens is an agentic AI web application with:

- `ai-report-frontend`: React + Vite frontend
- `ai-report-backend`: Python FastAPI backend with Gemini integration

## Project Structure

```text
AI_Lens/
  ai-report-frontend/
  ai-report-backend/
```

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+ (recommended 3.11 or 3.12)
- Git

## 1) Backend Setup

```bash
cd ai-report-backend
python -m venv .venv
```

Activate virtual environment:

- Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` file (or copy from `.env.example`) with:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.1-flash-lite
PORT=8000
ALLOWED_ORIGIN=http://localhost:5173
```

Run backend:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

## 2) Frontend Setup

```bash
cd ai-report-frontend
npm install
```

Create `.env` file (or copy from `.env.example`):

```env
VITE_API_BASE_URL=http://localhost:8000
```

Run frontend:

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

## 3) Build

Frontend production build:

```bash
cd ai-report-frontend
npm run build
```

## 4) API Endpoints

- `GET /health`
- `POST /reports/generate`
- `GET /reports/history`
- `POST /agent/chat`

## 5) Notes

- Do not commit `.env` files or API keys.
- Keep backend running on `127.0.0.1:8000` and frontend on `5173`.
- If port `8000` is busy, stop the old process or update both backend port and `VITE_API_BASE_URL`.

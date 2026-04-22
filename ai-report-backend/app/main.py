from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    ChatRequest,
    ChatResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportHistoryItem,
)
from .services.agent import ReportAgent
from .services.gemini_client import GeminiClient
from .services.storage import ReportStorage

load_dotenv()

app = FastAPI(title="AI Lens Backend", version="1.0.0")

allowed_origin = os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_path = Path(__file__).resolve().parent.parent / "reports.db"
storage = ReportStorage(db_path=db_path)
agent = ReportAgent(gemini_client=GeminiClient())


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/reports/generate", response_model=ReportGenerateResponse)
def generate_report(payload: ReportGenerateRequest) -> ReportGenerateResponse:
    report = agent.generate_report(topic=payload.topic, period=payload.period)
    storage.save_report(report)
    return ReportGenerateResponse(**report)


@app.get("/reports/history", response_model=List[ReportHistoryItem])
def report_history() -> List[ReportHistoryItem]:
    history = storage.history(limit=30)
    return [ReportHistoryItem(**item) for item in history]


@app.post("/agent/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    answer = agent.answer_question(payload.question)
    return ChatResponse(**answer)

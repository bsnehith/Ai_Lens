from typing import List, Optional

from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=180)
    period: str = Field(default="weekly")


class HighlightItem(BaseModel):
    type: str
    title: str
    impact: str
    source: str


class ReportMetrics(BaseModel):
    total_articles_reviewed: int
    high_impact_items: int
    categories_covered: int


class ReportGenerateResponse(BaseModel):
    id: str
    title: str
    generated_at: str
    summary: str
    highlights: List[HighlightItem]
    metrics: ReportMetrics
    next_actions: List[str]


class ReportHistoryItem(BaseModel):
    id: str
    title: str
    date: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class ChatSource(BaseModel):
    title: str
    url: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource] = []

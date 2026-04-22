from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from .gemini_client import GeminiClient
from .tools import fetch_ai_news, get_now_iso


class ReportAgent:
    def __init__(self, gemini_client: GeminiClient) -> None:
        self.gemini_client = gemini_client

    def generate_report(self, topic: str, period: str) -> Dict:
        news = fetch_ai_news(limit=24)

        fallback = self._fallback_report(topic=topic, period=period, news=news)
        prompt = self._report_prompt(topic=topic, period=period, news=news)
        result = self.gemini_client.generate_json(prompt=prompt, fallback=fallback)

        # Ensure required fields even if model returns partial data.
        result["id"] = str(uuid4())
        result["generated_at"] = get_now_iso()
        if "title" not in result:
            result["title"] = f"{period.title()} AI Industry Report"
        if "summary" not in result:
            result["summary"] = fallback["summary"]
        result["highlights"] = _safe_highlights(result.get("highlights", fallback["highlights"]))
        result["metrics"] = _safe_metrics(result.get("metrics", fallback["metrics"]), news_len=len(news))
        result["next_actions"] = _safe_actions(result.get("next_actions", fallback["next_actions"]))
        return result

    def answer_question(self, question: str) -> Dict:
        news = fetch_ai_news(limit=16)
        fallback = self._fallback_answer(question=question, news=news)
        prompt = self._chat_prompt(question=question, news=news)
        result = self.gemini_client.generate_json(prompt=prompt, fallback=fallback)

        answer = result.get("answer") if isinstance(result.get("answer"), str) else fallback["answer"]
        raw_sources = result.get("sources", fallback["sources"])
        sources = []
        if isinstance(raw_sources, list):
            for item in raw_sources[:5]:
                if isinstance(item, dict):
                    title = str(item.get("title", "")).strip()
                    url = str(item.get("url", "")).strip()
                    if title:
                        sources.append({"title": title, "url": url or None})
        if not sources:
            sources = fallback["sources"]
        return {"answer": answer, "sources": sources}

    def _report_prompt(self, topic: str, period: str, news: List[Dict]) -> str:
        return (
            "You are an AI industry analyst agent. "
            "Use the provided latest headlines and generate strictly valid JSON with this schema:\n"
            "{"
            '"title": string, '
            '"summary": string, '
            '"highlights": [{"type": string, "title": string, "impact": "High|Medium|Low", "source": string}], '
            '"metrics": {"total_articles_reviewed": number, "high_impact_items": number, "categories_covered": number}, '
            '"next_actions": [string]'
            "}\n\n"
            f"Topic: {topic}\nPeriod: {period}\nCurrent date: {datetime.utcnow().isoformat()}Z\n"
            f"Headlines: {news[:20]}\n"
            "Rules: keep summary 3-5 sentences, keep 4-6 highlights, keep 3 next_actions."
        )

    def _chat_prompt(self, question: str, news: List[Dict]) -> str:
        return (
            "You are an AI industry Q&A agent. Return strictly valid JSON:\n"
            '{"answer": string, "sources": [{"title": string, "url": string}]}\n'
            f"Question: {question}\n"
            f"Headlines context: {news[:16]}\n"
            "Rules: answer in plain concise English, no markdown."
        )

    def _fallback_report(self, topic: str, period: str, news: List[Dict]) -> Dict:
        highlights = []
        for item in news[:5]:
            highlights.append(
                {
                    "type": _guess_type(item["title"]),
                    "title": item["title"],
                    "impact": "Medium",
                    "source": item["source"],
                }
            )
        if not highlights:
            highlights = [
                {
                    "type": "Industry Update",
                    "title": "No live news found; run again later for latest sources.",
                    "impact": "Low",
                    "source": "System",
                }
            ]
        return {
            "id": str(uuid4()),
            "title": f"{period.title()} AI Report: {topic}",
            "generated_at": get_now_iso(),
            "summary": (
                "This report summarizes recent movements in the AI ecosystem including product releases, "
                "policy trends, and strategic investments."
            ),
            "highlights": highlights,
            "metrics": {
                "total_articles_reviewed": len(news),
                "high_impact_items": max(1, len(highlights) // 2),
                "categories_covered": len({_guess_type(h['title']) for h in highlights}),
            },
            "next_actions": [
                "Track pricing and capability updates from major model providers.",
                "Monitor policy announcements affecting enterprise deployment.",
                "Review competitor launches and map product positioning gaps.",
            ],
        }

    def _fallback_answer(self, question: str, news: List[Dict]) -> Dict:
        sources = [{"title": item["title"], "url": item["url"]} for item in news[:4]]
        if not sources:
            sources = [{"title": "No external sources available", "url": None}]
        return {
            "answer": (
                f"Based on current tracked signals, your question was: '{question}'. "
                "The latest AI updates indicate active model launches, enterprise adoption momentum, "
                "and continuing policy discussions around transparency and governance."
            ),
            "sources": sources,
        }


def _guess_type(title: str) -> str:
    lowered = title.lower()
    if any(k in lowered for k in ["raise", "funding", "series", "investment"]):
        return "Funding"
    if any(k in lowered for k in ["policy", "law", "regulation", "act"]):
        return "Policy"
    if any(k in lowered for k in ["launch", "release", "model", "llm"]):
        return "Model Release"
    return "Industry Update"


def _safe_highlights(value: object) -> List[Dict]:
    output: List[Dict] = []
    if isinstance(value, list):
        for item in value[:6]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            output.append(
                {
                    "type": str(item.get("type", "Industry Update")).strip() or "Industry Update",
                    "title": title,
                    "impact": str(item.get("impact", "Medium")).strip() or "Medium",
                    "source": str(item.get("source", "Unknown")).strip() or "Unknown",
                }
            )
    return output or [
        {
            "type": "Industry Update",
            "title": "No highlights returned by model.",
            "impact": "Low",
            "source": "System",
        }
    ]


def _safe_metrics(value: object, news_len: int) -> Dict[str, int]:
    if isinstance(value, dict):
        return {
            "total_articles_reviewed": int(value.get("total_articles_reviewed", news_len)),
            "high_impact_items": int(value.get("high_impact_items", max(1, news_len // 3))),
            "categories_covered": int(value.get("categories_covered", 3)),
        }
    return {
        "total_articles_reviewed": news_len,
        "high_impact_items": max(1, news_len // 3),
        "categories_covered": 3,
    }


def _safe_actions(value: object) -> List[str]:
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        if cleaned:
            return cleaned[:4]
    return [
        "Track high-impact announcements over the next 7 days.",
        "Validate major claims against original source links.",
        "Update leadership with concise strategic implications.",
    ]

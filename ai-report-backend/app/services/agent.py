from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from .gemini_client import GeminiClient
from .mcp_tools import TOOL_DECLARATIONS, execute_tool
from .tools import fetch_ai_news, get_now_iso, search_ai_news


class ReportAgent:
    def __init__(self, gemini_client: GeminiClient) -> None:
        self.gemini_client = gemini_client

    def generate_report(self, topic: str, period: str) -> Dict:
        news = fetch_ai_news(limit=24)

        fallback = self._fallback_report(topic=topic, period=period, news=news)
        prompt = self._report_prompt(topic=topic, period=period)
        result = self.gemini_client.generate_json_with_tools(
            user_prompt=prompt,
            fallback=fallback,
            tool_declarations=TOOL_DECLARATIONS,
            tool_executor=execute_tool,
            system_instruction=(
                "You are an agentic AI analyst. Use function tools to gather data first, "
                "then return strict JSON only."
            ),
        )

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
        prompt = self._chat_prompt(question=question)
        result = self.gemini_client.generate_json_with_tools(
            user_prompt=prompt,
            fallback=fallback,
            tool_declarations=TOOL_DECLARATIONS,
            tool_executor=execute_tool,
            system_instruction=(
                "You are an AI industry Q&A assistant. Use tools as needed and return strict JSON only."
            ),
        )

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
        if _is_weak_answer(answer) and sources:
            answer = _build_grounded_answer(question=question, sources=sources)
        return {"answer": answer, "sources": sources}

    def _report_prompt(self, topic: str, period: str) -> str:
        return (
            "Generate a periodic AI industry report and use tools for evidence collection.\n"
            "Return strictly valid JSON with this schema:\n"
            "{"
            '"title": string, '
            '"summary": string, '
            '"highlights": [{"type": string, "title": string, "impact": "High|Medium|Low", "source": string}], '
            '"metrics": {"total_articles_reviewed": number, "high_impact_items": number, "categories_covered": number}, '
            '"next_actions": [string]'
            "}\n\n"
            f"Topic: {topic}\nPeriod: {period}\nCurrent date: {datetime.utcnow().isoformat()}Z\n"
            "Rules:\n"
            "1) Call tools to fetch and inspect latest news.\n"
            "2) Keep summary 3-5 sentences.\n"
            "3) Keep 4-6 highlights.\n"
            "4) Keep exactly 3 next_actions.\n"
            "5) Output must be strict JSON."
        )

    def _chat_prompt(self, question: str) -> str:
        return (
            "Answer user question about latest AI industry updates.\n"
            "Always use tools before answering.\n"
            "First call search_ai_news with a keyword derived from question.\n"
            "Then call fetch_ai_news if additional context is needed.\n"
            "Return strictly valid JSON:\n"
            '{"answer": string, "sources": [{"title": string, "url": string}]}\n'
            f"Question: {question}\n"
            "Rules: answer in plain concise English, no markdown, max 6 lines."
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
        keyword = _question_keyword(question)
        focused = search_ai_news(keyword=keyword, limit=6) if keyword else []
        source_items = focused if focused else news
        sources = [{"title": item["title"], "url": item["url"]} for item in source_items[:5]]
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


def _question_keyword(question: str) -> str:
    lowered = question.lower()
    if any(word in lowered for word in ["funding", "raise", "series", "investment"]):
        return "funding"
    if any(word in lowered for word in ["launch", "model", "llm"]):
        return "model"
    if any(word in lowered for word in ["policy", "regulation", "law"]):
        return "policy"
    if any(word in lowered for word in ["security", "phishing", "attack"]):
        return "security"
    return "ai"


def _is_weak_answer(answer: str) -> bool:
    lowered = answer.lower().strip()
    weak_phrases = [
        "i couldn't find",
        "i could not find",
        "no specific",
        "sorry",
        "would you like to try a different keyword",
    ]
    return any(phrase in lowered for phrase in weak_phrases)


def _build_grounded_answer(question: str, sources: List[Dict]) -> str:
    top_titles = [src.get("title", "").strip() for src in sources if src.get("title")]
    top_titles = [title for title in top_titles if title][:3]
    if not top_titles:
        return (
            f"Based on recent AI updates for '{question}', there are relevant developments "
            "across models, enterprise adoption, and market activity."
        )

    joined = "; ".join(top_titles)
    return (
        f"Based on current tracked AI updates for '{question}', key relevant signals include: "
        f"{joined}. These indicate active momentum in the AI ecosystem this week."
    )

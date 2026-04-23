from __future__ import annotations

import logging
from typing import Any, Dict, List

from .tools import fetch_ai_news, search_ai_news, top_ai_sources

logger = logging.getLogger(__name__)

# These declarations are passed to Gemini as callable tools.
TOOL_DECLARATIONS: List[Dict[str, Any]] = [
    {
        "name": "fetch_ai_news",
        "description": "Fetch latest AI industry headlines from configured RSS sources.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "limit": {
                    "type": "INTEGER",
                    "description": "Maximum number of headlines to return.",
                }
            },
        },
    },
    {
        "name": "search_ai_news",
        "description": "Search latest AI headlines by keyword phrase.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "keyword": {
                    "type": "STRING",
                    "description": "Keyword to match against headline title.",
                },
                "limit": {
                    "type": "INTEGER",
                    "description": "Maximum number of matching headlines to return.",
                },
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "top_ai_sources",
        "description": "Get top source domains for latest AI headlines.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "limit": {
                    "type": "INTEGER",
                    "description": "Maximum number of source domains to return.",
                }
            },
        },
    },
]


def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Executes one tool by name and returns structured result."""
    args = args or {}
    logger.info("tool.execute.start name=%s args=%s", name, args)

    if name == "fetch_ai_news":
        limit = int(args.get("limit", 20))
        result = {"items": fetch_ai_news(limit=max(1, min(limit, 40)))}
        logger.info("tool.execute.done name=%s item_count=%s", name, len(result["items"]))
        return result

    if name == "search_ai_news":
        keyword = str(args.get("keyword", "")).strip()
        limit = int(args.get("limit", 8))
        result = {"items": search_ai_news(keyword=keyword, limit=max(1, min(limit, 20)))}
        logger.info("tool.execute.done name=%s item_count=%s", name, len(result["items"]))
        return result

    if name == "top_ai_sources":
        limit = int(args.get("limit", 5))
        result = {"items": top_ai_sources(limit=max(1, min(limit, 10)))}
        logger.info("tool.execute.done name=%s item_count=%s", name, len(result["items"]))
        return result

    logger.warning("tool.execute.unknown name=%s", name)
    return {"error": f"Unknown tool: {name}"}

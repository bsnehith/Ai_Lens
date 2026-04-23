from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List
from xml.etree import ElementTree

import requests

RSS_SOURCES = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://www.wired.com/feed/tag/ai/latest/rss",
]


def fetch_ai_news(limit: int = 20) -> List[Dict[str, str]]:
    """Simple MCP-style tool: fetch latest AI news from RSS feeds."""
    items: List[Dict[str, str]] = []

    for source in RSS_SOURCES:
        try:
            response = requests.get(source, timeout=10)
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
            entries = root.findall(".//item")
            if not entries:
                entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for entry in entries[:8]:
                title = _text_from_tag(entry, ["title", "{http://www.w3.org/2005/Atom}title"])
                link = _text_from_tag(entry, ["link", "{http://www.w3.org/2005/Atom}link"])
                if not link:
                    link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
                    if link_elem is not None:
                        link = link_elem.attrib.get("href", "")
                published = _text_from_tag(
                    entry,
                    ["pubDate", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"],
                )
                if title:
                    items.append(
                        {
                            "title": title.strip(),
                            "url": link.strip() if link else source,
                            "source": _extract_host(source),
                            "published_at": published.strip() if published else "",
                        }
                    )
        except requests.RequestException:
            continue
        except ElementTree.ParseError:
            continue

    deduped: List[Dict[str, str]] = []
    seen = set()
    for item in items:
        key = item["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break

    return deduped


def search_ai_news(keyword: str, limit: int = 8) -> List[Dict[str, str]]:
    """Tool: filter latest AI news by keyword."""
    clean_keyword = (keyword or "").strip().lower()
    if not clean_keyword:
        return []
    news = fetch_ai_news(limit=30)
    matches = [item for item in news if clean_keyword in item["title"].lower()]
    return matches[: max(1, min(limit, 15))]


def top_ai_sources(limit: int = 5) -> List[Dict[str, str]]:
    """Tool: return top source domains by article count."""
    news = fetch_ai_news(limit=50)
    counts = Counter(item["source"] for item in news)
    ranked = counts.most_common(max(1, min(limit, 10)))
    return [{"source": source, "count": str(count)} for source, count in ranked]


def get_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_host(url: str) -> str:
    cleaned = url.replace("https://", "").replace("http://", "")
    return cleaned.split("/")[0]


def _text_from_tag(node: ElementTree.Element, tag_names: List[str]) -> str:
    for tag_name in tag_names:
        tag = node.find(tag_name)
        if tag is not None and tag.text:
            return tag.text
    return ""

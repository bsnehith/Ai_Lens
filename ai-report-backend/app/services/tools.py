from __future__ import annotations

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

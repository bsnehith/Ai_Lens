from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests


class GeminiClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def generate_json(self, prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Calls Gemini and expects JSON output. Falls back safely when unavailable."""
        if not self.configured:
            return fallback

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "responseMimeType": "application/json",
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=25)
            response.raise_for_status()
            data = response.json()
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            if not text:
                return fallback
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
            return fallback
        except (requests.RequestException, ValueError, KeyError, IndexError):
            return fallback

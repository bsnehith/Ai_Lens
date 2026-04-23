from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Regex to strip markdown code fences that Gemini sometimes wraps JSON in.
_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


class GeminiClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def api_url(self) -> str:
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

    def generate_json(self, prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Calls Gemini and expects JSON output. Falls back safely when unavailable."""
        if not self.configured:
            return fallback

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "responseMimeType": "application/json",
            },
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=25)
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
            parsed = _safe_parse_json(text)
            if isinstance(parsed, dict):
                return parsed
            return fallback
        except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
            logger.warning("gemini.generate_json.error %s", exc)
            return fallback

    def generate_json_with_tools(
        self,
        *,
        user_prompt: str,
        fallback: Dict[str, Any],
        tool_declarations: List[Dict[str, Any]],
        tool_executor: Callable[[str, Dict[str, Any]], Dict[str, Any]],
        system_instruction: Optional[str] = None,
        max_tool_rounds: int = 4,
    ) -> Dict[str, Any]:
        """Tool-calling loop: model invokes tools and then returns final JSON."""
        if not self.configured:
            return fallback

        contents: List[Dict[str, Any]] = [{"role": "user", "parts": [{"text": user_prompt}]}]
        forced_tool_config = self._tool_config_force_any(tool_declarations)
        tool_calls_seen = 0

        for round_num in range(max_tool_rounds):
            # First round: force the LLM to call a tool (mode=ANY).
            # After at least one tool call: switch to AUTO so it can return text.
            tool_config = (
                forced_tool_config if tool_calls_seen == 0 else self._tool_config_auto()
            )

            # Once tool results are in context, ask for JSON output strictly.
            generation_config: Dict[str, Any] = {"temperature": 0.3}
            if tool_calls_seen > 0:
                generation_config["responseMimeType"] = "application/json"

            payload: Dict[str, Any] = {
                "contents": contents,
                "tools": [{"functionDeclarations": tool_declarations}],
                "generationConfig": generation_config,
                "toolConfig": tool_config,
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            try:
                response = requests.post(self.api_url, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as exc:
                logger.error("gemini.tool_loop.request_error round=%s error=%s", round_num, exc)
                return fallback

            parts = self._extract_parts(data)
            if not isinstance(parts, list) or not parts:
                logger.warning("gemini.tool_loop.empty_parts round=%s", round_num)
                return fallback

            function_calls = [
                part["functionCall"]
                for part in parts
                if isinstance(part, dict) and part.get("functionCall")
            ]
            if function_calls:
                tool_calls_seen += len(function_calls)
                logger.info(
                    "llm.tool_calls.detected round=%s count=%s",
                    round_num,
                    len(function_calls),
                )
                contents.append({"role": "model", "parts": parts})
                function_responses: List[Dict[str, Any]] = []
                for function_call in function_calls:
                    name = str(function_call.get("name", ""))
                    args = function_call.get("args", {})
                    if not isinstance(args, dict):
                        args = {}
                    logger.info("llm.tool_call.invoke name=%s args=%s", name, args)
                    result = tool_executor(name, args)
                    function_responses.append(
                        {
                            "functionResponse": {
                                "name": name,
                                "response": {"result": result},
                            }
                        }
                    )
                contents.append({"role": "user", "parts": function_responses})
                continue

            # If no function call occurred yet, reject this response and continue
            # because assignment requires explicit LLM tool invocation.
            if tool_calls_seen == 0:
                logger.warning("llm.response.without_tools round=%s retrying", round_num)
                continue

            parsed = self._parse_json_text_from_parts(parts)
            if parsed:
                logger.info(
                    "llm.final_json.ready round=%s tool_calls_seen=%s",
                    round_num,
                    tool_calls_seen,
                )
                return parsed
            logger.warning("llm.final_json.parse_failed round=%s", round_num)
            return fallback

        logger.warning(
            "llm.tool_loop.exhausted max_tool_rounds=%s fallback_used",
            max_tool_rounds,
        )
        return fallback

    def _extract_parts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )

    def _parse_json_text_from_parts(self, parts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Concatenate all text parts and parse as JSON.
        Handles markdown code fences defensively.
        """
        text_parts = [
            part["text"]
            for part in parts
            if isinstance(part, dict) and part.get("text")
        ]
        final_text = "\n".join(text_parts).strip()
        if not final_text:
            return None
        return _safe_parse_json(final_text)

    def _tool_config_force_any(self, tool_declarations: List[Dict[str, Any]]) -> Dict[str, Any]:
        names = [tool.get("name", "") for tool in tool_declarations if isinstance(tool, dict) and tool.get("name")]
        return {
            "functionCallingConfig": {
                "mode": "ANY",
                "allowedFunctionNames": names,
            }
        }

    def _tool_config_auto(self) -> Dict[str, Any]:
        return {
            "functionCallingConfig": {
                "mode": "AUTO",
            }
        }


def _safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON that may be wrapped in markdown code fences.
    Returns None if parsing fails.
    """
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except ValueError:
        pass

    match = _CODE_FENCE_RE.search(text)
    if match:
        inner = match.group(1).strip()
        try:
            parsed = json.loads(inner)
            if isinstance(parsed, dict):
                return parsed
        except ValueError:
            pass

    return None

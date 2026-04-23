from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Regex to strip markdown code fences that Gemini sometimes wraps JSON in.
_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


class GeminiClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.fallback_models = self._parse_fallback_models(
            os.getenv(
                "GEMINI_FALLBACK_MODELS",
                "gemini-2.5-flash,gemini-3.1-flash-lite,gemini-3-flash,gemini-3.1-pro",
            )
        )
        self.allowed_models = {
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-3-flash",
            "gemini-3.1-pro",
        }
        self.model_cooldown_until: Dict[str, float] = {}

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def api_url(self) -> str:
        return self._api_url_for_model(self.model)

    def _api_url_for_model(self, model_name: str) -> str:
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={self.api_key}"
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
            request_result = self._request_with_model_fallback(payload=payload, timeout=25, round_num=0)
            if request_result is None:
                return fallback
            data, used_model = request_result
            logger.info("gemini.generate_json.model_used model=%s", used_model)
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
        collected_tool_items: List[Dict[str, Any]] = []

        for round_num in range(max_tool_rounds):
            # First round: force the LLM to call a tool (mode=ANY).
            # After at least one tool call: switch to AUTO so it can return text.
            tool_config = (
                forced_tool_config if tool_calls_seen == 0 else self._tool_config_auto()
            )

            # Keep config simple in tool rounds for better model compatibility.
            generation_config: Dict[str, Any] = {"temperature": 0.3}

            payload: Dict[str, Any] = {
                "contents": contents,
                "tools": [{"functionDeclarations": tool_declarations}],
                "generationConfig": generation_config,
                "toolConfig": tool_config,
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            request_result = self._request_with_model_fallback(
                payload=payload,
                timeout=30,
                round_num=round_num,
            )
            if request_result is None:
                return fallback
            data, used_model = request_result
            logger.info("gemini.tool_loop.model_used round=%s model=%s", round_num, used_model)

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
                    items = result.get("items", []) if isinstance(result, dict) else []
                    if isinstance(items, list):
                        collected_tool_items.extend([item for item in items if isinstance(item, dict)])
                    function_responses.append(
                        {
                            "functionResponse": {
                                "name": name,
                                "response": {"result": result},
                            }
                        }
                    )
                # Use role=tool for function responses for better compatibility.
                contents.append({"role": "tool", "parts": function_responses})
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
            # If strict JSON parsing fails but this is chat-shaped output,
            # preserve model answer text instead of returning generic fallback.
            text_only = self._extract_text_from_parts(parts)
            if text_only and _looks_like_chat_fallback_shape(fallback):
                logger.warning(
                    "llm.final_json.parse_failed round=%s using_text_answer_fallback",
                    round_num,
                )
                return {"answer": text_only, "sources": _items_to_sources(collected_tool_items)}
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

    def _extract_text_from_parts(self, parts: List[Dict[str, Any]]) -> str:
        text_parts = [
            part["text"]
            for part in parts
            if isinstance(part, dict) and part.get("text")
        ]
        return "\n".join(text_parts).strip()

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

    def _parse_fallback_models(self, value: str) -> List[str]:
        models = [item.strip() for item in value.split(",") if item.strip()]
        deduped: List[str] = []
        for model_name in models:
            if model_name not in deduped:
                deduped.append(model_name)
        return deduped

    def _candidate_models(self) -> List[str]:
        candidates = [self.model, *self.fallback_models]
        unique: List[str] = []
        now = time.time()
        for candidate in candidates:
            if not candidate:
                continue
            if candidate not in self.allowed_models:
                continue
            cooldown_until = self.model_cooldown_until.get(candidate, 0.0)
            if cooldown_until > now:
                continue
            if candidate not in unique:
                unique.append(candidate)
        return unique

    def _request_with_model_fallback(
        self,
        *,
        payload: Dict[str, Any],
        timeout: int,
        round_num: int,
    ) -> Optional[tuple[Dict[str, Any], str]]:
        last_exception: Optional[Exception] = None
        for model_name in self._candidate_models():
            try:
                response = requests.post(self._api_url_for_model(model_name), json=payload, timeout=timeout)
                response.raise_for_status()
                return response.json(), model_name
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else "unknown"
                error_body = exc.response.text if exc.response is not None else ""
                logger.error(
                    "gemini.tool_loop.request_error round=%s model=%s status=%s error=%s body=%s",
                    round_num,
                    model_name,
                    status,
                    exc,
                    error_body,
                )
                last_exception = exc
                if status in (429, 503):
                    delay = _extract_retry_delay_seconds(error_body)
                    if delay > 0:
                        # Cool down this model to avoid repeatedly hitting quota/availability errors.
                        self.model_cooldown_until[model_name] = time.time() + delay
                    if delay > 0:
                        time.sleep(min(delay, 2.0))
                continue
            except requests.RequestException as exc:
                logger.error(
                    "gemini.tool_loop.request_exception round=%s model=%s error=%s",
                    round_num,
                    model_name,
                    exc,
                )
                last_exception = exc
                continue

        if last_exception is not None:
            logger.error("gemini.tool_loop.all_models_failed round=%s", round_num)
        return None


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

    # Attempt 3: parse first JSON object embedded in free text.
    candidate = _extract_first_json_object(text)
    if candidate:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except ValueError:
            pass

    return None


def _extract_retry_delay_seconds(error_body: str) -> float:
    if not error_body:
        return 0.0

    # Match messages like: "Please retry in 13.455365713s."
    match = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", error_body, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return 0.0

    # Match JSON retry field style: "retryDelay": "13s"
    match = re.search(r'"retryDelay"\s*:\s*"([0-9]+)s"', error_body)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return 0.0

    return 0.0


def _extract_first_json_object(text: str) -> Optional[str]:
    """
    Extract first balanced {...} block from mixed text.
    This handles cases where model returns prose around JSON.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _looks_like_chat_fallback_shape(fallback: Dict[str, Any]) -> bool:
    return isinstance(fallback, dict) and "answer" in fallback and "sources" in fallback


def _items_to_sources(items: List[Dict[str, Any]]) -> List[Dict[str, Optional[str]]]:
    sources: List[Dict[str, Optional[str]]] = []
    for item in items[:6]:
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        url = str(item.get("url", "")).strip() or None
        sources.append({"title": title, "url": url})
    return sources

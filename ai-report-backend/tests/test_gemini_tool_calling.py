import unittest
from unittest.mock import Mock, patch

from app.services.gemini_client import GeminiClient


class GeminiToolCallingTests(unittest.TestCase):
    @patch("app.services.gemini_client.requests.post")
    def test_generate_json_with_tools_invokes_executor(self, mock_post: Mock) -> None:
        # Round 1: model asks for tool call
        round_one_response = Mock()
        round_one_response.raise_for_status.return_value = None
        round_one_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "fetch_ai_news",
                                    "args": {"limit": 3},
                                }
                            }
                        ]
                    }
                }
            ]
        }

        # Round 2: model returns final JSON answer
        round_two_response = Mock()
        round_two_response.raise_for_status.return_value = None
        round_two_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"answer":"ok","sources":[{"title":"src","url":"https://x.com"}]}'
                            }
                        ]
                    }
                }
            ]
        }

        mock_post.side_effect = [round_one_response, round_two_response]

        client = GeminiClient()
        client.api_key = "dummy"  # force configured path

        executor_calls = []

        def fake_executor(name, args):
            executor_calls.append((name, args))
            return {"items": [{"title": "a"}]}

        output = client.generate_json_with_tools(
            user_prompt="answer question",
            fallback={"answer": "fallback", "sources": []},
            tool_declarations=[{"name": "fetch_ai_news", "parameters": {"type": "OBJECT"}}],
            tool_executor=fake_executor,
            max_tool_rounds=3,
        )

        self.assertEqual(output["answer"], "ok")
        self.assertEqual(len(executor_calls), 1)
        self.assertEqual(executor_calls[0][0], "fetch_ai_news")


if __name__ == "__main__":
    unittest.main()

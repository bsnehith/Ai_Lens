# AI Lens Backend

Backend service for AI Lens built with FastAPI and Gemini, implementing real
LLM tool/function invocation for:

- AI industry periodic reports
- AI industry Q&A chat answers

---

## 1) What This Backend Does

This service receives frontend requests, runs an agentic tool-calling loop with
Gemini, executes model-selected tools, and returns structured JSON responses.

Main business workflows:

1. Generate AI report (`POST /reports/generate`)
2. Answer AI trend chat (`POST /agent/chat`)
3. Return report history (`GET /reports/history`)

---

## 2) Project Layout

```text
ai-report-backend/
  app/
    main.py                    # FastAPI app + routes
    schemas.py                 # Request/response contracts
    services/
      agent.py                 # Report/chat orchestration
      gemini_client.py         # Gemini API + function-calling loop
      mcp_tools.py             # Tool schema declarations + dispatcher
      tools.py                 # Tool implementations (RSS/news/source stats)
      storage.py               # SQLite report storage
  tests/
    test_gemini_tool_calling.py
  .env.example
  requirements.txt
```

---

## 3) Setup

```bash
cd ai-report-backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 4) Environment

Copy `.env.example` to `.env` and set values:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
PORT=8000
ALLOWED_ORIGIN=http://localhost:5173
```

Notes:

- `GEMINI_API_KEY` is required for live LLM behavior.
- If LLM/model fails, backend returns safe fallback responses.
- Never commit real `.env` secrets.

---

## 5) Run

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## 6) Endpoints

- `GET /health`
- `POST /reports/generate`
- `GET /reports/history`
- `POST /agent/chat`

Example requests:

```bash
curl -X POST "http://127.0.0.1:8000/reports/generate" -H "Content-Type: application/json" -d "{\"topic\":\"AI weekly\",\"period\":\"weekly\"}"
curl -X POST "http://127.0.0.1:8000/agent/chat" -H "Content-Type: application/json" -d "{\"question\":\"What changed in AI this week?\"}"
```

---

## 7) Complete Working Flow

### A) Report flow

1. `main.py` receives `POST /reports/generate`
2. `agent.py -> ReportAgent.generate_report()` runs
3. agent builds prompt + fallback
4. calls `GeminiClient.generate_json_with_tools(...)`
5. Gemini receives:
   - prompt
   - tool schema declarations
   - forced first tool call config (`mode=ANY`)
6. Gemini emits `functionCall`
7. backend dispatcher executes tool
8. backend sends `functionResponse` back to Gemini
9. Gemini returns final JSON report
10. report is normalized + stored in SQLite
11. API returns report to frontend

### B) Chat flow

1. `main.py` receives `POST /agent/chat`
2. `agent.py -> ReportAgent.answer_question()` runs
3. same tool-calling loop executes
4. model may call one or multiple tools
5. final JSON answer + sources returned to frontend

---

## 8) Tool Calling Implementation (Core Requirement)

Files and responsibilities:

- `app/services/gemini_client.py`
  - builds Gemini payload with `tools`
  - detects model `functionCall`
  - executes tool via dispatcher callback
  - appends `functionResponse`
  - loops until final JSON response
- `app/services/mcp_tools.py`
  - `TOOL_DECLARATIONS` passed to Gemini
  - `execute_tool(...)` dispatcher by tool name
- `app/services/tools.py`
  - concrete tool implementations:
    - `fetch_ai_news`
    - `search_ai_news`
    - `top_ai_sources`

This is true model-driven tool invocation, not utility-only calling.

---

## 9) How To Prove Tool Invocation

Trigger a report/chat request and inspect backend logs.

Expected log lines:

- `llm.tool_calls.detected ...`
- `llm.tool_call.invoke name=...`
- `tool.execute.start name=...`
- `tool.execute.done name=...`
- `llm.final_json.ready ...`

These prove:

1. model requested tool,
2. backend executed tool,
3. model consumed tool result,
4. model produced final output.

---

## 10) Tests

Run:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

`tests/test_gemini_tool_calling.py` validates function-calling loop behavior by
mocking Gemini tool-call + final JSON responses.

---

## 11) Troubleshooting

### A) Slow response / fallback messages

Possible reasons:

- model endpoint unavailable
- temporary provider error (e.g. 503)
- invalid key or model name
- RSS source latency

Check logs for:

- `gemini.tool_loop.request_error ...`
- `llm.tool_loop.exhausted ... fallback_used`

### B) Port already in use

If backend fails with bind error, stop existing process on 8000 or run another port.

### C) Frontend says backend offline

Check:

- backend is running
- frontend env points to correct backend URL
- CORS origin matches frontend URL

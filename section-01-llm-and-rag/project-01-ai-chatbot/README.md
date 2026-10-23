# Project 1 — Cloud-Based AI Chatbot

## 1. Project Overview

A command-line and REST API chatbot backed by Anthropic's Claude models. Built as a learning project to understand the full architecture of a cloud-LLM-backed application: provider integration, conversation state, error handling, testing, and exposing the same logic through both a CLI and a web API.

## 2. Learning Objectives

- Understand how a cloud LLM API call works end-to-end (model vs. endpoint vs. SDK).
- Practice separating presentation logic from provider/service logic.
- Manage conversation state and understand token-driven cost growth.
- Write unit tests that mock an external API instead of calling it.
- Expose the same business logic through both a CLI and a FastAPI REST service.
- Apply basic security and cost-management practices for LLM-backed applications.

See [`docs/project-01-ai-chatbot-concepts.md`](../../docs/project-01-ai-chatbot-concepts.md) at the repo root for interview-style Q&A on every concept below.

## 3. Features

- Command-line chatbot with multi-turn conversation history and a `reset` command.
- REST API (`POST /chat`, `GET /health`) built with FastAPI.
- Input validation (rejects empty/blank messages before calling the LLM).
- Typed error handling translated into safe, user-facing messages.
- Token usage and estimated per-call cost logged automatically.
- Unit test suite (pytest) that mocks the Anthropic API — no real calls, no cost.

## 4. Architecture

```
┌──────────────────┐
│  CLI (main.py)    │──┐
└──────────────────┘  │     ┌───────────────────┐      ┌──────────────────┐
                        ├───▶│  llm_client.py     │─────▶│   Claude API      │
┌──────────────────┐  │     │  - client instance  │      │  (Anthropic)      │
│  FastAPI (api.py)  │──┘     │  - send_message()   │◀─────│  runs the model    │
│  POST /chat        │        │  - error translation│      └──────────────────┘
│  GET /health        │        └───────────────────┘
└──────────────────┘
```

Both entry points call the same `send_message()` function in `llm_client.py` — provider logic lives in exactly one place.

## 5. Technology Stack

- Python 3.13
- [`anthropic`](https://pypi.org/project/anthropic/) — official Claude Python SDK
- `python-dotenv` — environment-based configuration
- FastAPI + Uvicorn — REST API layer
- pytest + `unittest.mock` — automated testing
- Git / GitHub — version control

## 6. Prerequisites

- Python 3.10+ installed and on `PATH`
- Git
- An [Anthropic Console](https://console.anthropic.com) account with billing/credits set up, and a **workspace-scoped** API key (not an org-wide/admin key)

## 7. Installation (Windows / PowerShell)

```powershell
cd "E:\Workspace\ai-engineering-roadmap\section-01-llm-and-rag\project-01-ai-chatbot"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 8. Environment Configuration

Copy the example file and fill in your real key — never commit `.env`:

```powershell
Copy-Item .env.example .env
```

`.env`:
```
ANTHROPIC_API_KEY=your_actual_key_here
```

## 9. Running the Chatbot (CLI)

```powershell
python -m app.main
```

Type a question, use `reset` to clear conversation history, and `exit` to quit.

## 10. Running the FastAPI Service

```powershell
uvicorn app.api:app --reload
```

Interactive API docs (Swagger UI): http://127.0.0.1:8000/docs

## 11. Example Requests and Responses

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/health -Method Get
```
```json
{"status": "ok"}
```

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -ContentType "application/json" -Body '{"message": "What is 2+2?"}'
```
```json
{"response": "4"}
```

A blank message returns `422 Unprocessable Entity`; an LLM-side failure (auth, rate limit, network) returns `502 Bad Gateway` with a sanitized error detail.

## 12. Testing

```powershell
pytest -v
```

All tests mock the Anthropic client (`app.llm_client._client.messages.create`) and the FastAPI route's `send_message` call — no real API requests, no token cost, runs in a couple of seconds.

## 13. Security Considerations

- API key lives only in `.env` (gitignored); `.env.example` documents the required variable name with a placeholder.
- Client timeout set to 30s; authentication failures are never retried (permanent failure).
- Error messages returned to callers are static, sanitized strings — never raw provider response bodies, stack traces, or the API key.
- Token usage and estimated cost are logged server-side only, never included in API responses.

## 14. Known Limitations

- Conversation history is in-memory only (CLI) and not persisted; the REST API is stateless per request (no multi-turn memory over HTTP).
- No context-window truncation strategy for very long conversations.
- No streaming responses.
- No authentication or rate-limiting on the FastAPI layer itself.

## 15. Future Enhancements

- Session-based conversation history over the REST API.
- Streaming responses (SSE) for the API and CLI.
- Swap-in alternative providers behind the same `llm_client` interface.
- Persist conversation history to a database.

## 16. Concepts Learned

Cloud LLM API fundamentals, model/endpoint/SDK distinctions, token-based billing, stateless-vs-stateful conversation design, service-layer separation of concerns, typed exception translation, mocking external APIs in unit tests, FastAPI request/response validation, and basic LLM cost/security management. Full interview-style explanations: [`docs/project-01-ai-chatbot-concepts.md`](../../docs/project-01-ai-chatbot-concepts.md).

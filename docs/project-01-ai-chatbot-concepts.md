# Project 1 — AI Chatbot: Concepts & Interview Q&A

Deep explanations for everything built in `section-01-llm-and-rag/project-01-ai-chatbot/`, written as interview-ready answers. Code walkthroughs were kept out of chat during implementation — this is where they live.

---

## 1. LLM & Cloud API Fundamentals

**Q: What is an LLM?**
A Large Language Model is a neural network trained on large amounts of text to predict the next token given preceding context. You interact with it through natural-language text, not typed method signatures — there's no fixed schema for *what* it can answer, only for *how* you structure the request (the API contract).

**Q: What is a cloud LLM API, and how does it differ from running a model locally (e.g. Ollama)?**
A cloud LLM API means the model weights and inference run on the provider's infrastructure (Anthropic's GPUs, in this project). Your application sends an HTTPS request with a prompt and receives generated text back. Running locally (Ollama) means the weights and inference execute on your own machine — no network call, no per-token billing, but you're limited by local hardware and model size.

**Q: What's the difference between a model, an API endpoint, and an SDK?**

| Concept | Definition | Spring Boot / Java analogy |
|---|---|---|
| Model | The trained neural network that generates text (e.g. `claude-sonnet-5-5`) | Business logic running on a server you don't control |
| API endpoint | The URL + JSON contract exposed by the provider (`POST /v1/messages`) | A REST endpoint on someone else's microservice |
| SDK | The client library (`anthropic` package) that builds requests, adds auth headers, and parses responses | A generated REST client / Feign client wrapper around `RestTemplate` |

**Q: What is an API key, and how does authentication work?**
An API key is a secret bearer token that identifies your account to the API, sent as an `Authorization` header on every request. It's conceptually identical to a bearer token passed to any third-party REST API — the key difference here is *you* are the client calling someone else's service. If it leaks, anyone can make billed calls on your account, which is why it must never be committed to source control.

**Q: Is a Claude.ai / ChatGPT subscription the same as API access?**
No — they're separate products with separate billing. A `claude.ai` Pro subscription (or ChatGPT Plus) grants access to the consumer chat web app only. API access is pay-as-you-go, billed per token, through a separate Console account (console.anthropic.com / platform.openai.com) that needs its own funded credits.

**Q: What are tokens, and what's the difference between input and output tokens?**
A token is roughly ¾ of an English word — the model operates on tokens, not raw characters. **Input tokens** are everything sent in the prompt (system instructions + conversation history + the new message) and are billed at one rate; **output tokens** are what the model generates in response, typically billed at a higher rate. Total cost per call = `(input_tokens × input_price) + (output_tokens × output_price)`.

**Q: How does model selection affect cost, latency, and quality?**
Smaller/cheaper models (e.g. Haiku tier) are faster and far cheaper per token but weaker on complex reasoning; larger flagship models (e.g. Opus/Fable tier) cost more and respond slower but handle harder tasks better. Sonnet-tier models sit in between as the default "best balance" choice. The right choice depends on the task's complexity relative to acceptable cost and latency — not just picking the most capable model by default.

**Q: Walk through the request lifecycle for calling a cloud LLM.**
1. Application builds a prompt (system + history + new message).
2. SDK attaches the API key as an auth header and serializes the request to JSON.
3. HTTPS POST to the provider's endpoint.
4. Provider authenticates the key, runs inference on the model.
5. Provider returns a JSON response (generated text + token usage).
6. SDK deserializes the JSON into typed objects.

This is architecturally identical to a Spring `@Service` calling an external REST API via `RestTemplate`/`WebClient` — build request → auth header → send → receive JSON → deserialize → handle 4xx/5xx/timeouts. The only novelty is that the "business logic" on the other end is a language model.

---

## 2. Architecture & Separation of Concerns

**Q: Why split `main.py` and `llm_client.py` instead of one file?**
`main.py` is the **presentation/control layer** — it owns input/output and the application loop, with zero knowledge of which LLM provider is used. `llm_client.py` is the **service layer** — it owns the client instance, model selection, and provider-specific error translation, with zero knowledge of how input was collected or displayed. This mirrors a Spring Boot `@RestController` calling a `@Service`: swapping the LLM provider later only touches `llm_client.py`; swapping the entry point (CLI → REST API) only adds a new caller, it never touches the service layer.

**Q: What's the benefit in practice?**
When Phase 7 added a FastAPI layer, `llm_client.py` required zero changes — proof the abstraction boundary was drawn correctly. Two entry points (`main.py` CLI, `api.py` REST) both call the same `send_message()` function instead of duplicating business logic, the same way a Controller and a `CommandLineRunner` in Spring Boot would both call the same injected `@Service` bean.

**Q: Why wrap Anthropic's SDK exceptions in a custom `LLMError`?**
This is **exception translation** — the caller (`main.py` or the FastAPI route) only needs to know "the LLM layer failed, here's a safe message," not which of five Anthropic-specific exception types occurred. It's the same pattern as a Spring `@Service` catching a third-party client's checked exceptions and re-throwing a domain-specific `ServiceException`: callers depend on *your* contract, not the vendor SDK's.

---

## 3. Conversation History & State

**Q: What's the difference between stateless and stateful interactions with an LLM?**
Each API call is inherently stateless — the model has no memory between calls. **We** simulate statefulness by resending the growing list of prior messages (`user`/`assistant` turns) on every request, so the model has the context needed to answer follow-ups correctly.

**Q: What are the three message roles, and what's each for?**
- `system` — instructions that shape overall behavior/persona, set once, separate from the message list.
- `user` — the human's messages.
- `assistant` — the model's prior replies, resent so the model "remembers" what it already said.

**Q: Why does resending full history on every turn increase cost, and what limits it?**
Every turn re-sends the *entire* conversation as input tokens, so a 20-turn conversation costs far more per-turn than turn 1 — cost grows roughly linearly with conversation length. This is ultimately bounded by the model's **context window** (the maximum tokens it can process in a single request); a long-running conversation would eventually need truncation or summarization, which this project does not implement (a known limitation — history lives only in an in-memory Python list and is lost on exit).

---

## 4. Testing

**Q: What's the difference between a unit test and an integration test here?**
A unit test (what this project uses) mocks the Anthropic client entirely (`patch("app.llm_client._client.messages.create", ...)`) and verifies *our* logic — history forwarding, error translation, response parsing — with no network call, no cost, running in milliseconds. An integration test would hit the real API to verify the SDK's actual contract still holds; slower, costs tokens, and intentionally not automated in this project's test suite.

**Q: Why mock at the `_client.messages.create` level specifically, rather than mocking `send_message` itself?**
Mocking the SDK call lets the test exercise the *real* `send_message()` logic — including the try/except chain that translates each Anthropic exception into `LLMError` — rather than bypassing it. Mocking `send_message` would only prove the test file compiles, not that the error-translation logic is correct.

---

## 5. REST API Design (FastAPI)

**Q: Describe the request flow once the chatbot is exposed over REST.**
Client → `POST /chat` (FastAPI route in `api.py`) → Pydantic validates the request body → `llm_client.send_message()` → Anthropic API → response parsed → `ChatResponse` schema serialized back to the client. Identical shape to a Spring Boot `@RestController` method delegating to a `@Service`, with Pydantic playing the role of `@Valid` + a DTO/record class.

**Q: How is input validation handled, and what HTTP status does invalid input get?**
A Pydantic `field_validator` on `ChatRequest.message` strips whitespace and raises if the result is empty. FastAPI/Pydantic turns that validation failure into an automatic **422 Unprocessable Entity** response — no manual `if` check needed in the route handler, the same way Bean Validation annotations (`@NotBlank`) produce automatic 400s in Spring.

**Q: Why return 502 (not 500) when the LLM call fails?**
502 Bad Gateway semantically means "this server, acting as a gateway, got an invalid response from an upstream server." That's exactly the relationship here — our API is a thin proxy in front of Anthropic's API, so an upstream LLM failure is a 502, not a 500 (which would imply a bug in our own code).

---

## 6. Security & Cost Management

**Q: Why must an API key never be committed to Git, and how is that enforced here?**
A committed key is permanently in the repository's history (even if later deleted, it's recoverable from old commits) and visible to anyone with repo access — including public GitHub scrapers that actively hunt for leaked keys to abuse. It's enforced by keeping the key only in `.env` (loaded via `python-dotenv`), with `.env` listed in `.gitignore`; `.env.example` (committed) documents the required variable name without a real value.

**Q: How are errors kept "safe" (not leaking secrets or internals)?**
`LLMError` messages are static, hand-written strings (e.g. `"Rate limit exceeded. Please wait and try again."`) — never the raw Anthropic response body, stack trace, or key value. The FastAPI layer passes that same sanitized string into `HTTPException(detail=...)`, so a client of the REST API sees a clear but safe message, never internal details.

**Q: How are timeouts and retries configured, and why not retry everything?**
The client has an explicit 30-second timeout (the SDK's default is 10 minutes, too long for an interactive chatbot). The Anthropic SDK automatically retries transient failures — connection errors, 429 rate limits, 5xx server errors — twice by default, but does **not** retry `AuthenticationError` (401), since a bad API key is a permanent failure that retrying cannot fix. Retrying permanent failures wastes time and, in some designs, could even trigger rate limiting.

**Q: How is cost tracked and estimated?**
Every response includes a `usage` object (`input_tokens`, `output_tokens`). `llm_client.py` logs both counts plus an estimated cost computed from the current model's published per-million-token pricing (`cost = (input_tokens/1e6)×input_price + (output_tokens/1e6)×output_price`). This is visible in the terminal/server logs only — never returned in the API response body, keeping the client-facing contract minimal.

**Q: How does this project avoid unnecessary API calls (and therefore unnecessary cost)?**
Both the CLI and the REST API reject empty/blank input *before* calling the LLM — the CLI loop re-prompts on a blank line, and the FastAPI validator returns 422 for a blank `message`, so no API request (and no cost) is incurred for input that was never going to produce a meaningful answer.

---

## 7. Known Limitations (honest answers for "what would you improve?")

- Conversation history is in-memory only — lost on process restart, no persistence layer.
- No context-window truncation/summarization strategy for very long conversations.
- No per-user/session isolation in the FastAPI layer — every `/chat` call is independent and stateless (by design, per the Phase 7 scope), so multi-turn memory only exists in the CLI.
- No streaming responses — the API waits for the full completion before responding, which is fine for short answers but would feel slow for long ones.
- No authentication/rate-limiting on the FastAPI layer itself — it trusts whoever can reach it, which is acceptable for a local learning project but not for a public deployment.

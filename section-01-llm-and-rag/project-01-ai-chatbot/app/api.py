import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

from app.llm_client import LLMError, send_message

logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title="AI Chatbot API")


class ChatRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message must not be empty")
        return v


class ChatResponse(BaseModel):
    response: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        answer = send_message([{"role": "user", "content": request.message}])
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(response=answer)

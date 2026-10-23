import logging

import anthropic
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 1024
TIMEOUT_SECONDS = 30.0
SYSTEM_PROMPT = "You are a helpful, concise assistant."

PRICING_PER_MTOK = {
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00},
}

_client = Anthropic(timeout=TIMEOUT_SECONDS)


class LLMError(Exception):
    """Raised when a request to the LLM provider fails."""


def _log_usage(usage) -> None:
    prices = PRICING_PER_MTOK.get(MODEL)
    if prices is None:
        logger.info("Tokens used - input: %d, output: %d", usage.input_tokens, usage.output_tokens)
        return

    cost = (usage.input_tokens / 1_000_000) * prices["input"] + (usage.output_tokens / 1_000_000) * prices["output"]
    logger.info(
        "Tokens used - input: %d, output: %d | estimated cost: $%.6f",
        usage.input_tokens,
        usage.output_tokens,
        cost,
    )


def send_message(messages: list[dict]) -> str:
    try:
        response = _client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
    except anthropic.AuthenticationError as exc:
        raise LLMError("Authentication failed. Check your ANTHROPIC_API_KEY.") from exc
    except anthropic.RateLimitError as exc:
        raise LLMError("Rate limit exceeded. Please wait and try again.") from exc
    except anthropic.APITimeoutError as exc:
        raise LLMError("The request timed out. Please try again.") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMError("Could not reach the Anthropic API. Check your network connection.") from exc
    except anthropic.APIStatusError as exc:
        raise LLMError(f"Anthropic API returned an error (status {exc.status_code}).") from exc

    _log_usage(response.usage)

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "".join(text_parts)

import logging

from app.llm_client import LLMError, send_message

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main() -> None:
    print("AI Chatbot (type 'exit' to leave, 'reset' to clear history)\n")

    history: list[dict] = []

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            print("Please enter a question.\n")
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if user_input.lower() == "reset":
            history.clear()
            print("Conversation history cleared.\n")
            continue

        history.append({"role": "user", "content": user_input})

        try:
            answer = send_message(history)
        except LLMError as exc:
            print(f"[Error] {exc}\n")
            history.pop()
            continue

        history.append({"role": "assistant", "content": answer})
        print(f"Claude: {answer}\n")


if __name__ == "__main__":
    main()

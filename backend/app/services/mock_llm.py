"""Pluggable mock reply generator. Replace with real LLM later."""

TONE_INTROS: dict[str, str] = {
    "formal": (
        "Thank you for your message. I am writing to acknowledge receipt and provide "
        "the following response."
    ),
    "concise": "Thanks — quick reply below.",
    "friendly": "Hi! Thanks for reaching out — here’s a quick note back.",
}


def generate_mock_reply(
    *,
    thread_snippet: str,
    subject: str,
    tone: str,
    signature: str,
) -> str:
    intro = TONE_INTROS.get(tone.lower(), "Thanks for your message.")
    body = f"{intro}\n\n[Mock draft — replace with real LLM]\n\nRe: {subject or '(no subject)'}\n"
    if thread_snippet:
        body += f"\nContext (truncated):\n{thread_snippet[:2000]}\n"
    if signature.strip():
        body += f"\n{signature}\n"
    return body

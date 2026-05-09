"""Offline reply stubs when no LLM API key is configured.

Produces plain reply bodies only: no subject line, no “context” dumps, no dev placeholders.
Set ``OPENAI_API_KEY`` for AI-generated replies.
"""

from __future__ import annotations

import re
import unicodedata


def _subject_hint(subject: str, max_len: int = 72) -> str:
    s = (subject or "").strip()
    if s.lower().startswith("re:"):
        s = s[3:].strip()
    s = re.sub(r"\s+", " ", s)
    if len(s) > max_len:
        s = s[: max_len - 3].rstrip() + "..."
    return s or "your message"


def _clean_snippet(text: str, max_len: int = 320) -> str:
    """Strip invisible chars and trim so we never paste raw newsletter MIME noise."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:max_len]


def _greeting(
    *,
    first_name: str | None,
    relationship: str,
    user_tone: str,
) -> str:
    """Opening line: casual first-name hi when the thread reads friendly."""
    rel = (relationship or "professional").lower()
    ut = (user_tone or "concise").lower()
    name = (first_name or "").strip()
    if rel == "friendly" and name:
        # Mirror quick chats ("Hii Vishal" → "hi kumar,")
        return f"hi {name.lower()},"
    if rel == "friendly":
        return "hi,"
    if ut == "friendly" and name:
        return f"Hi {name},"
    if name and ut != "formal":
        return f"Hi {name},"
    if name:
        return f"Dear {name},"
    return "Hi,"


def generate_mock_reply(
    *,
    thread_snippet: str,
    subject: str,
    tone: str,
    signature: str,
    correspondent_first_name: str | None = None,
    relationship_style: str = "professional",
) -> str:
    hint = _subject_hint(subject)
    snippet = _clean_snippet(thread_snippet)
    t = (tone or "concise").lower()
    rel = (relationship_style or "professional").lower()

    greet = _greeting(
        first_name=correspondent_first_name,
        relationship=relationship_style,
        user_tone=tone,
    )

    # When the relationship is casual, keep copy warm even if the user picked "concise".
    if rel == "friendly":
        if t == "formal":
            core_body = (
                f"Thank you for your note about {hint}. "
                "I have received it and will come back to you shortly."
            )
        elif t == "concise":
            core_body = (
                "thanks — saw your message. i'll reply properly in a bit."
            )
        else:
            core_body = (
                f"thanks for the note about {hint} — i'll read it properly and get back to you."
            )
        core = f"{greet}\n\n{core_body}"
    elif t == "formal":
        core = (
            f"Thank you for your email regarding {hint}. "
            "I have received it and will review it as soon as I am able."
        )
    elif t == "friendly":
        core = (
            f"{greet}\n\n"
            f"Thanks for sending this — I saw your note about {hint}. "
            "I'll read through it properly soon."
        )
    else:
        # concise + professional (default)
        if snippet and len(snippet) > 40:
            core = (
                f"{greet}\n\n"
                f"Thanks — got your message about {hint}. "
                "I'll take a look and reach out if I need anything."
            )
        else:
            core = (
                f"{greet}\n\n"
                f"Thanks for your note about {hint}. "
                "I'll follow up if needed."
            )

    lines = [core.rstrip()]
    if signature.strip():
        lines.append("")
        lines.append(signature.strip())
    return "\n".join(lines)

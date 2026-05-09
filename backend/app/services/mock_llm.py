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


def generate_mock_reply(
    *,
    thread_snippet: str,
    subject: str,
    tone: str,
    signature: str,
) -> str:
    hint = _subject_hint(subject)
    snippet = _clean_snippet(thread_snippet)
    t = (tone or "concise").lower()

    # Short, human-shaped stubs — only what would appear in the outgoing body (no headers, no labels).
    if t == "formal":
        core = (
            f"Thank you for your email regarding {hint}. "
            "I have received it and will review it as soon as I am able."
        )
    elif t == "friendly":
        core = (
            f"Hi,\n\nThanks for sending this — I saw your note about {hint}. "
            "I'll read through it properly soon.\n\nBest,"
        )
    else:
        # concise (default)
        if snippet and len(snippet) > 40:
            core = (
                f"Thanks — got your message about {hint}. "
                "I'll take a look and reach out if I need anything."
            )
        else:
            core = (
                f"Thanks for your note about {hint}. "
                "I'll follow up if needed."
            )

    lines = [core]
    if signature.strip():
        lines.append("")
        lines.append(signature.strip())
    return "\n".join(lines)

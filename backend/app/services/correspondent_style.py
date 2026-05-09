"""Infer casual vs professional rapport from prior messages; blend with user-selected tone."""

from __future__ import annotations

import re
import unicodedata

_CASUAL = re.compile(
    r"(?i)\b(hi{2,}|hii+|hey|hello|yo\b|hola\b|sup\b|wassup|"
    r"thanks\b|thank you\b|thx\b|ty\b|cheers\b|lol\b|haha\b|"
    r"cool\b|nice\b|awesome\b)\b"
)
_FORMAL = re.compile(
    r"(?i)\b(dear\b|sir\b|madam|greetings\b|sincerely\b|kind regards\b|"
    r"best regards\b|respectfully\b|yours faithfully\b)\b"
)
_TITLE = frozenset({"mr", "mrs", "ms", "miss", "dr", "prof"})


def extract_correspondent_email(from_addr: str | None) -> str:
    if not from_addr:
        return ""
    s = from_addr.strip()
    if "<" in s and ">" in s:
        return s.split("<", 1)[1].split(">", 1)[0].strip().lower()
    return s.lower()


def display_first_name_from_from_header(from_addr: str | None) -> str | None:
    """Best-effort first name from `Name <email>` for greetings."""
    if not from_addr:
        return None
    s = from_addr.strip()
    if "<" in s:
        s = s.split("<", 1)[0].strip().strip('"').strip("'")
    if not s:
        return None
    parts = s.split()
    if not parts:
        return None
    first = parts[0].rstrip(",")
    if first.lower().rstrip(".") in _TITLE and len(parts) > 1:
        first = parts[1].rstrip(",")
    # Drop email-looking tokens
    if "@" in first:
        return None
    first = re.sub(r"^[^\w]+|[^\w]+$", "", first, flags=re.UNICODE)
    return first or None


def _norm(s: str) -> str:
    t = unicodedata.normalize("NFKC", s or "")
    t = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]", "", t)
    return t.lower()


def _is_bulk_address(email: str) -> bool:
    e = (email or "").lower()
    return any(
        x in e
        for x in (
            "noreply",
            "no-reply",
            "donotreply",
            "newsletter",
            "notifications@",
            "marketing@",
        )
    )


def infer_relationship_style(
    *,
    correspondent_email: str,
    their_texts: list[str],
    latest_incoming: str,
) -> str:
    """Return ``friendly`` or ``professional``."""
    if _is_bulk_address(correspondent_email):
        return "professional"

    blob = _norm(" ".join(their_texts + [latest_incoming]))
    if not blob.strip():
        return "professional"

    score = 0
    if _CASUAL.search(blob):
        score += 2
    if _FORMAL.search(blob):
        score -= 2
    # Very short, informal openers ("Hii Vishal")
    li = (latest_incoming or "").strip()
    if len(li) < 100 and _CASUAL.search(li):
        score += 3
    if len(li) < 60 and not _FORMAL.search(li) and re.search(r"(?i)^\s*h+i+", li):
        score += 2

    return "friendly" if score > 0 else "professional"


def build_tone_blend_instruction(*, user_tone: str, relationship: str) -> str:
    """Natural-language rules for the LLM (and docs)."""
    ut = (user_tone or "concise").lower()
    rel = (relationship or "professional").lower()

    chunks: list[str] = []
    if rel == "friendly":
        chunks.append(
            "Recent mail with this person reads casual/friendly. "
            "Mirror that: greet with their first name when you have it, "
            "use a natural opener (hi/hey), and avoid stiff corporate closings unless they use them."
        )
    else:
        chunks.append(
            "Recent mail with this person reads professional or is from a bulk/system address. "
            "Use business-appropriate language."
        )

    if ut == "concise" and rel == "friendly":
        chunks.append(
            "The user chose CONCISE: keep the reply short (a few sentences), "
            "but stay warm and human—not curt or formal."
        )
    elif ut == "friendly" and rel == "professional":
        chunks.append(
            "The user chose FRIENDLY: be warm and approachable while staying appropriate for work email."
        )
    elif ut == "formal" and rel == "friendly":
        chunks.append(
            "The user chose FORMAL: be polite and clear without sounding cold; "
            "you may still use their first name if the thread is clearly on a first-name basis."
        )
    elif ut == "concise":
        chunks.append("The user chose CONCISE: be brief and direct.")
    elif ut == "formal":
        chunks.append("The user chose FORMAL: structured and polite.")
    elif ut == "friendly":
        chunks.append("The user chose FRIENDLY: warm and conversational.")

    return " ".join(chunks)

"""Reply draft text via OpenAI Chat Completions when ``OPENAI_API_KEY`` is set; else ``mock_llm``."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from app.core.config import get_settings
from app.services import mock_llm

_log = logging.getLogger(__name__)

# Stay within typical context limits; Gmail body is often enough below this.
MAX_BODY_CHARS = 12_000


def generate_reply_draft(
    *,
    from_addr: str | None,
    subject: str | None,
    body_text: str | None,
    tone: str,
    signature: str,
    custom_instructions: str | None,
    style_examples: Sequence[str] | None,
    correspondent_first_name: str | None = None,
    relationship_style: str = "professional",
    tone_blend_instruction: str = "",
    correspondent_history: Sequence[str] | None = None,
) -> str:
    settings = get_settings()
    key = (settings.openai_api_key or "").strip()
    truncated = (body_text or "")[:MAX_BODY_CHARS]
    if not key:
        return mock_llm.generate_mock_reply(
            thread_snippet=truncated,
            subject=subject or "",
            tone=tone,
            signature=signature,
            correspondent_first_name=correspondent_first_name,
            relationship_style=relationship_style,
        )
    try:
        return _openai_generate(
            api_key=key,
            model=(settings.openai_model or "gpt-4o-mini").strip(),
            from_addr=from_addr or "(unknown)",
            subject=subject or "(no subject)",
            body_text=truncated.strip(),
            tone=tone,
            signature=signature.strip(),
            custom_instructions=(custom_instructions or "").strip(),
            style_examples=list(style_examples or []),
            correspondent_first_name=correspondent_first_name,
            relationship_style=relationship_style,
            tone_blend_instruction=(tone_blend_instruction or "").strip(),
            correspondent_history=list(correspondent_history or []),
        )
    except Exception:
        _log.exception("OpenAI draft generation failed")
        raise


def _openai_generate(
    *,
    api_key: str,
    model: str,
    from_addr: str,
    subject: str,
    body_text: str,
    tone: str,
    signature: str,
    custom_instructions: str,
    style_examples: list[str],
    correspondent_first_name: str | None,
    relationship_style: str,
    tone_blend_instruction: str,
    correspondent_history: list[str],
) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    system = (
        "You write email replies on behalf of the mailbox owner. "
        "Output only the reply body as plain text (no Subject line, no markdown code fences). "
        "Never repeat or paste the email Subject as its own line in the body. "
        "Do not include sections such as 'Context (truncated)', quoted headers, or bulk-forwarded newsletter text; "
        "write a normal reply as a real person would. "
        "Respond appropriately to the correspondent's message. "
        "Do not invent facts, meetings, or commitments not supported by the thread. "
        "Infer rapport from the samples: if they write casually, you may use hi + first name and light closings; "
        "if the thread is professional or from automated senders, stay businesslike. "
        "Tone knobs: formal = polite and structured; concise = brief and direct; friendly = warm. "
        "When instructions say the relationship is casual but the user asked for concise, be short AND warm, not stiff."
    )

    parts: list[str] = []
    if correspondent_history:
        parts.append("### Earlier messages from this correspondent (match their style; do not quote verbatim)")
        for i, ex in enumerate(correspondent_history[:6], 1):
            parts.append(f"--- Prior {i} ---\n{ex[:1000]}")
        parts.append("")
    parts.extend(
        [
            "### Email you are replying to",
            f"From (correspondent): {from_addr}",
            f"Subject: {subject}",
        ]
    )
    if correspondent_first_name:
        parts.append(f"Correspondent first name (for greetings): {correspondent_first_name}")
    parts.extend(
        [
            "",
            "### Their message / thread body",
            body_text if body_text else "(no body text — use subject and snippet context only)",
            "",
            f"### Inferred relationship style: {relationship_style}",
        ]
    )
    if tone_blend_instruction:
        parts.extend(["", "### How to blend tone", tone_blend_instruction])
    parts.extend(
        [
            "",
            f"### Requested reply tone (user control): {tone}",
        ]
    )
    if custom_instructions:
        parts.extend(["", "### Extra instructions from the user", custom_instructions])
    if signature:
        parts.extend(
            [
                "",
                "### Signature",
                "Append this exact signature block at the end of your reply (unless it would be redundant):",
                signature,
            ]
        )
    if style_examples:
        parts.append("")
        parts.append(
            "### Samples of this user's recent outgoing mail (match voice lightly; do not copy verbatim)"
        )
        for i, ex in enumerate(style_examples[:3], 1):
            parts.append(f"--- Sample {i} ---\n{ex[:1200]}")

    user_content = "\n".join(parts)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        temperature=0.65,
        max_tokens=1400,
    )
    choice = resp.choices[0].message.content
    if not choice or not str(choice).strip():
        raise ValueError("Model returned an empty reply")
    text = str(choice).strip()
    if signature and signature not in text:
        text = f"{text.rstrip()}\n\n{signature}"
    return text

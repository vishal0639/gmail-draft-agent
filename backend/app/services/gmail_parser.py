import base64

# Gmail API returns payload with parts; extract best-effort plain text and html


def _b64url_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def get_header(headers: list[dict] | None, name: str) -> str | None:
    if not headers:
        return None
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value")
    return None


def _walk_parts(
    part: dict,
) -> tuple[str | None, str | None, str | None, str | None, str | None, str | None]:  # noqa: PLR0911
    """Recursively return (text, html, in_reply, refs, to, rfc message_id) from a part tree."""
    mime = (part.get("mimeType") or "").lower()
    text_out: str | None = None
    html_out: str | None = None
    in_r: str | None = get_header(part.get("headers") or None, "In-Reply-To")
    refs: str | None = get_header(part.get("headers") or None, "References")
    to: str | None = get_header(part.get("headers") or None, "To")
    mid: str | None = get_header(part.get("headers") or None, "Message-ID")
    bdata = part.get("body", {}).get("data")
    if bdata and mime in ("text/plain", "message/rfc822", ""):
        try:
            text_out = _b64url_decode(bdata).decode("utf-8", errors="replace")
        except Exception:
            pass
    if bdata and mime in ("text/html",):
        try:
            html_out = _b64url_decode(bdata).decode("utf-8", errors="replace")
        except Exception:
            pass
    for p in part.get("parts") or ():
        t, h, ir, rf, tt, m = _walk_parts(p)
        in_r = in_r or ir
        refs = refs or rf
        to = to or tt
        mid = mid or m
        if not text_out and t:
            text_out = t
        if not html_out and h:
            html_out = h
    return text_out, html_out, in_r, refs, to, mid


def parse_gmail_message_resource(msg: dict) -> dict:
    """
    Return stable dict for our API: subject, from, body_text, body_html, rfc fields.
    `msg` is a Gmail users.messages.get(..., format='full') result.
    """
    payload = msg.get("payload") or {}
    headers = payload.get("headers") or []
    subject = get_header(headers, "Subject")
    from_ = get_header(headers, "From")
    in_reply = get_header(headers, "In-Reply-To")
    references = get_header(headers, "References")
    to = get_header(headers, "To")
    message_id_rfc = get_header(headers, "Message-Id")
    t, h, w_ir, w_rf, w_to, w_mid = _walk_parts(payload)
    in_reply = in_reply or w_ir
    references = references or w_rf
    to = to or w_to
    message_id_rfc = message_id_rfc or w_mid
    if not t and not h and payload.get("body", {}).get("data"):
        d = _b64url_decode(payload["body"]["data"])
        if "text/html" in (payload.get("mimeType") or "").lower():
            h = d.decode("utf-8", errors="replace")
        else:
            t = d.decode("utf-8", errors="replace")
    return {
        "id": msg.get("id"),
        "thread_id": msg.get("threadId"),
        "label_ids": msg.get("labelIds") or [],
        "snippet": msg.get("snippet"),
        "internal_date": msg.get("internalDate"),
        "subject": subject,
        "from_addr": from_,
        "body_text": t,
        "body_html": h,
        "in_reply_to": in_reply,
        "references": references,
        "to_addresses": to,
        "message_id_rfc": message_id_rfc,
    }

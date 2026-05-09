"""
Gmail API v1 — single place for all `build('gmail','v1')` resource calls.

We use the official Google client (`googleapiclient.discovery.build`).

Gmail resources used in this app (REST reference: https://developers.google.com/gmail/api/reference/rest):

- ``users.getProfile`` — verify tokens / account email
- ``users.messages.list`` — list message ids (with ``q=`` for unread/recent)
- ``users.messages.get`` — full message (format=full) for body + headers
- ``users.messages.send`` — send raw RFC 822 in ``body.raw``; optional ``threadId``

OAuth scopes: see ``app.core.config.Settings.google_scopes`` (readonly, send, compose).

Parsing of MIME payloads (not a separate API) lives in ``gmail_parser.py``.
"""

from __future__ import annotations

import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.gmail_parser import parse_gmail_message_resource

_log = logging.getLogger(__name__)


def get_gmail_service(creds: Credentials):
    """Build the Gmail v1 service object (used by all other functions in this module)."""
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def get_user_profile(service) -> dict[str, Any]:  # noqa: ANN001
    """``users.getProfile`` — e.g. ``emailAddress`` for the authenticated account."""
    return service.users().getProfile(userId="me").execute()


def send_rfc822_raw(
    service,
    raw_b64: str,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """``users.messages.send`` — base64url-encoded RFC 822 message; keep thread with ``threadId``."""
    body: dict = {"raw": raw_b64}
    if thread_id:
        body["threadId"] = thread_id
    return service.users().messages().send(userId="me", body=body).execute()


def list_messages(
    service,
    *,
    filter_kind: str,
    max_results: int,
    page_token: str | None = None,
) -> tuple[list[dict[str, Any]], int | None, str | None]:
    """List via ``users.messages.list``, then ``users.messages.get`` each id for the API response fields.

    Pass ``page_token`` from a previous response's ``nextPageToken`` for pagination.
    """
    q: str
    fk = (filter_kind or "unread").lower()
    if fk == "unread":
        q = "is:unread in:inbox"
    elif fk == "recent":
        q = "in:inbox newer_than:7d"
    elif fk == "all":
        q = "in:inbox"
    else:
        q = "is:unread in:inbox"
    list_kwargs: dict[str, Any] = {
        "userId": "me",
        "maxResults": max_results,
        "q": q,
    }
    if page_token:
        list_kwargs["pageToken"] = page_token
    try:
        res = service.users().messages().list(**list_kwargs).execute()
    except HttpError as e:
        _log.exception("Gmail list failed: %s", e)
        raise
    mids = [m["id"] for m in (res.get("messages") or [])]
    out: list[dict[str, Any]] = []
    for mid in mids:
        try:
            full = (
                service.users()
                .messages()
                .get(userId="me", id=mid, format="full")
                .execute()
            )
            p = parse_gmail_message_resource(full)
            out.append(
                {
                    "id": p["id"],
                    "thread_id": p["thread_id"],
                    "subject": p.get("subject"),
                    "from_addr": p.get("from_addr"),
                    "snippet": p.get("snippet"),
                    "internal_date": p.get("internal_date"),
                    "label_ids": p.get("label_ids") or [],
                }
            )
        except HttpError:
            continue
    next_page = res.get("nextPageToken")
    return out, res.get("resultSizeEstimate"), next_page


def fetch_recent_sent_style_snippets(
    service,
    *,
    max_messages: int = 3,
) -> list[str]:
    """Short excerpts from recent Sent mail to steer LLM tone/phrasing (case-study: learn from past sends)."""
    max_messages = max(1, min(max_messages, 5))
    try:
        res = (
            service.users()
            .messages()
            .list(userId="me", maxResults=max_messages, q="in:sent")
            .execute()
        )
    except HttpError:
        return []
    mids = [m["id"] for m in (res.get("messages") or [])][:max_messages]
    snippets: list[str] = []
    for mid in mids:
        try:
            full = (
                service.users()
                .messages()
                .get(userId="me", id=mid, format="full")
                .execute()
            )
            p = parse_gmail_message_resource(full)
            t = (p.get("body_text") or p.get("snippet") or "").strip()
            if t:
                snippets.append(t[:800])
        except HttpError:
            continue
    return snippets


def get_message_full(service, message_id: str) -> dict:
    """``users.messages.get`` with format=full, then parse payload in ``gmail_parser``."""
    full = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    return parse_gmail_message_resource(full)


def get_account_email(service) -> str:
    """Authenticated mailbox address (for telling our messages from the correspondent's)."""
    return (get_user_profile(service).get("emailAddress") or "").strip().lower()


def _email_from_from_header(from_addr: str | None) -> str:
    if not from_addr:
        return ""
    s = from_addr.strip()
    if "<" in s and ">" in s:
        return s.split("<", 1)[1].split(">", 1)[0].strip().lower()
    return s.lower()


def collect_correspondent_thread_messages(
    service,
    *,
    thread_id: str | None,
    correspondent_email: str,
    max_messages: int = 20,
    max_chars: int = 900,
) -> list[str]:
    """Chronological plain-text excerpts from the correspondent in this thread only."""
    if not thread_id or not correspondent_email:
        return []
    them = correspondent_email.strip().lower()
    try:
        thr = (
            service.users()
            .threads()
            .get(userId="me", id=thread_id, format="full")
            .execute()
        )
    except HttpError:
        return []
    msgs = sorted(
        thr.get("messages") or [],
        key=lambda m: int(m.get("internalDate") or 0),
    )
    if len(msgs) > max_messages:
        msgs = msgs[-max_messages:]
    out: list[str] = []
    for m in msgs:
        try:
            p = parse_gmail_message_resource(m)
        except Exception:
            continue
        em = _email_from_from_header(p.get("from_addr"))
        if em != them:
            continue
        chunk = (p.get("body_text") or p.get("snippet") or "").strip()
        if chunk:
            out.append(chunk[:max_chars])
    return out


def fetch_recent_incoming_from_address(
    service,
    *,
    correspondent_email: str,
    max_results: int = 6,
    max_chars: int = 600,
) -> list[str]:
    """Additional snippets from this sender (any thread) for style inference."""
    addr = (correspondent_email or "").strip()
    if "@" not in addr:
        return []
    q = f"from:{addr} newer_than:365d"
    try:
        res = (
            service.users()
            .messages()
            .list(userId="me", maxResults=max_results, q=q)
            .execute()
        )
    except HttpError:
        return []
    mids = [m["id"] for m in (res.get("messages") or [])]
    out: list[str] = []
    for mid in mids:
        try:
            full = (
                service.users()
                .messages()
                .get(userId="me", id=mid, format="full")
                .execute()
            )
            p = parse_gmail_message_resource(full)
        except HttpError:
            continue
        chunk = (p.get("body_text") or p.get("snippet") or "").strip()
        if chunk:
            out.append(chunk[:max_chars])
    return out

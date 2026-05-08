import base64
import json
import uuid
from email.message import EmailMessage

from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.db import models
from app.services import auth_service, draft_service, gmail_data


def _gmail_http_message(err: HttpError) -> str:
    try:
        raw = json.loads(err.content.decode()) if err.content else {}
        return (raw.get("error") or {}).get("message") or str(err)
    except Exception:  # noqa: BLE001
        return str(err) or getattr(err, "reason", None) or repr(err)


def _is_retryable_http(err: BaseException) -> bool:
    if isinstance(err, HttpError):
        try:
            code = int(err.resp.status)  # type: ignore[union-attr]
        except (TypeError, ValueError):
            return False
        return code in (429, 500, 502, 503, 504)
    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
    retry=retry_if_exception(_is_retryable_http),
    reraise=True,
)
def _send_raw(service, raw_b64: str, thread_id: str | None) -> dict:
    return gmail_data.send_rfc822_raw(service, raw_b64, thread_id)


def _build_rfc822(
    *,
    to: str,
    subject: str,
    body_text: str,
    in_reply_to: str | None,
    references: str | None,
) -> str:
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    msg.set_content(body_text, charset="utf-8")
    return msg.as_string()


def send_approved_draft(
    db: Session,
    user_id: str,
    draft_id: str,
    idempotency_key: str,
) -> dict:
    exist = (
        db.query(models.SendAttempt)
        .filter_by(user_id=user_id, idempotency_key=idempotency_key)
        .first()
    )
    if exist:
        return {
            "idempotent": True,
            "status": exist.status,
            "gmail_message_id": exist.gmail_message_id,
            "detail": exist.detail,
        }
    d = draft_service.get_draft(db, user_id, draft_id)
    if not d:
        raise KeyError("draft not found")
    if d.status != models.DraftStatus.APPROVED.value:
        raise ValueError("Only approved drafts can be sent (safety gate)")
    if not (d.to_addresses or "").strip():
        raise ValueError("Draft has no recipient (To). Edit the draft or regenerate from a valid message.")
    creds = auth_service.credentials_for_user(db, user_id)
    service = gmail_data.get_gmail_service(creds)
    raw = _build_rfc822(
        to=d.to_addresses or "",
        subject=d.subject,
        body_text=d.body,
        in_reply_to=d.in_reply_to_rfc,
        references=d.references_rfc,
    )
    raw_b64 = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")
    try:
        out = _send_raw(service, raw_b64, d.thread_id)
    except HttpError as e:
        msg = _gmail_http_message(e)
        att = models.SendAttempt(
            id=str(uuid.uuid4()),
            user_id=user_id,
            draft_id=d.id,
            idempotency_key=idempotency_key,
            status=models.SendAttemptStatus.FAILED.value,
            detail={"error": msg, "http_status": getattr(e.resp, "status", None)},
        )
        db.add(att)
        d.status = models.DraftStatus.FAILED.value
        d.error_message = msg[:2000]
        db.add(
            models.AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                event="send.failed",
                details={"draft_id": d.id, "error": msg[:500]},
            )
        )
        db.commit()
        raise ValueError(msg) from e
    except Exception as e:
        att = models.SendAttempt(
            id=str(uuid.uuid4()),
            user_id=user_id,
            draft_id=d.id,
            idempotency_key=idempotency_key,
            status=models.SendAttemptStatus.FAILED.value,
            detail={"error": str(e)},
        )
        db.add(att)
        d.status = models.DraftStatus.FAILED.value
        d.error_message = str(e)[:2000]
        db.add(
            models.AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                event="send.failed",
                details={"draft_id": d.id, "error": str(e)[:500]},
            )
        )
        db.commit()
        raise
    att = models.SendAttempt(
        id=str(uuid.uuid4()),
        user_id=user_id,
        draft_id=d.id,
        idempotency_key=idempotency_key,
        status=models.SendAttemptStatus.SUCCESS.value,
        gmail_message_id=out.get("id"),
        detail={"gmail": out},
    )
    db.add(att)
    db.add(
        models.AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event="send.success",
            details={"draft_id": d.id, "gmail_id": out.get("id")},
        )
    )
    draft_pk = d.id
    gmail_mid = out.get("id")
    detail_out = {"gmail": out}
    db.delete(d)
    db.commit()
    return {
        "idempotent": False,
        "status": models.SendAttemptStatus.SUCCESS.value,
        "gmail_message_id": gmail_mid,
        "detail": detail_out,
        "draft_id": draft_pk,
        "removed": True,
    }

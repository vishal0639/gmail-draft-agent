import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db import models
from app.schemas.draft import DraftGenerateRequest, ToneKind
from app.services import auth_service, gmail_data, llm_reply, preferences_service

# Pending: 24h from creation. After approve: must send by 48h from original creation.
# Rejected: removed 24h after dismissal.
PENDING_TTL = timedelta(days=1)
APPROVED_TTL_FROM_CREATION = timedelta(days=2)
REJECTED_RETENTION = timedelta(hours=24)


def generate_draft(
    db: Session,
    user_id: str,
    req: DraftGenerateRequest,
) -> models.Draft:
    purge_expired_drafts(db, user_id=user_id)
    creds = auth_service.credentials_for_user(db, user_id)
    service = gmail_data.get_gmail_service(creds)
    p = gmail_data.get_message_full(service, req.source_message_id)
    prefs = preferences_service.get_prefs_dict(db, user_id)
    sig = (prefs or {}).get("email_signature", "") or ""
    tone = (req.tone or ToneKind.CONCISE).value
    snippet = p.get("body_text") or p.get("snippet") or ""
    subj = p.get("subject") or ""
    style_hints = gmail_data.fetch_recent_sent_style_snippets(service, max_messages=3)
    body = llm_reply.generate_reply_draft(
        from_addr=p.get("from_addr"),
        subject=subj,
        body_text=snippet,
        tone=tone,
        signature=sig,
        custom_instructions=req.custom_instructions,
        style_examples=style_hints,
    )
    subj_out = subj
    if subj_out and not subj_out.lower().strip().startswith("re:"):
        subj_out = f"Re: {subj_out}"
    now = datetime.utcnow()
    d = models.Draft(
        id=str(uuid.uuid4()),
        user_id=user_id,
        thread_id=p.get("thread_id"),
        source_message_id=req.source_message_id,
        in_reply_to_rfc=p.get("message_id_rfc"),
        references_rfc=p.get("references"),
        to_addresses=_reply_to(p.get("from_addr")),
        subject=subj_out or "Re: (no subject)",
        body=body,
        tone=tone,
        status=models.DraftStatus.PENDING_REVIEW.value,
        expires_at=now + PENDING_TTL,
    )
    db.add(d)
    db.add(
        models.AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event="draft.created",
            details={"draft_id": d.id, "source_message_id": req.source_message_id},
        )
    )
    db.commit()
    db.refresh(d)
    return d


def _reply_to(from_addr: str | None) -> str:
    if not from_addr:
        return ""
    s = from_addr.strip()
    if "<" in s and ">" in s:
        return s.split("<", 1)[1].split(">", 1)[0].strip()
    return s


def _effective_expiry(d: models.Draft) -> datetime:
    if d.expires_at is not None:
        return d.expires_at
    if d.status == models.DraftStatus.REJECTED.value:
        return d.updated_at + REJECTED_RETENTION
    if d.status == models.DraftStatus.APPROVED.value:
        return d.created_at + APPROVED_TTL_FROM_CREATION
    return d.created_at + PENDING_TTL


def purge_expired_drafts(db: Session, *, user_id: str | None = None) -> int:
    """Remove drafts past expires_at, legacy SENT rows, and backfill missing expires_at."""
    now = datetime.utcnow()
    q_b = db.query(models.Draft)
    if user_id:
        q_b = q_b.filter(models.Draft.user_id == user_id)
    touched = False
    for d in q_b.filter(models.Draft.expires_at.is_(None)).all():
        if d.status == models.DraftStatus.REJECTED.value:
            d.expires_at = d.updated_at + REJECTED_RETENTION
        elif d.status == models.DraftStatus.APPROVED.value:
            d.expires_at = d.created_at + APPROVED_TTL_FROM_CREATION
        else:
            d.expires_at = d.created_at + PENDING_TTL
        touched = True

    q_all = db.query(models.Draft)
    if user_id:
        q_all = q_all.filter(models.Draft.user_id == user_id)
    to_remove: list[models.Draft] = []
    for d in q_all.all():
        if d.status == models.DraftStatus.SENT.value:
            to_remove.append(d)
            continue
        if _effective_expiry(d) <= now:
            to_remove.append(d)
    for d in to_remove:
        db.delete(d)
    if to_remove or touched:
        db.commit()
    return len(to_remove)


def get_draft(db: Session, user_id: str, draft_id: str) -> models.Draft | None:
    purge_expired_drafts(db, user_id=user_id)
    return (
        db.query(models.Draft)
        .filter_by(id=draft_id, user_id=user_id)
        .first()
    )


def list_drafts(
    db: Session,
    user_id: str,
    *,
    status: str | None = None,
    limit: int = 50,
) -> tuple[list[models.Draft], int]:
    purge_expired_drafts(db, user_id=user_id)
    q = db.query(models.Draft).filter_by(user_id=user_id)
    if status:
        q = q.filter_by(status=status)
    n = q.count()
    items = (
        q.order_by(models.Draft.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    return items, n


def update_draft_body(
    db: Session, user_id: str, draft_id: str, body: str, subject: str | None
) -> models.Draft:
    d = get_draft(db, user_id, draft_id)
    if not d:
        raise KeyError("draft not found")
    if d.status not in (
        models.DraftStatus.PENDING_REVIEW.value,
        models.DraftStatus.APPROVED.value,
    ):
        raise ValueError("Only pending or approved drafts can be edited")
    d.body = body
    if subject is not None:
        d.subject = subject
    d.updated_at = datetime.utcnow()
    db.add(
        models.AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event="draft.edited",
            details={"draft_id": d.id},
        )
    )
    db.commit()
    db.refresh(d)
    return d


def approve_draft(db: Session, user_id: str, draft_id: str) -> models.Draft:
    d = get_draft(db, user_id, draft_id)
    if not d:
        raise KeyError("draft not found")
    if d.status != models.DraftStatus.PENDING_REVIEW.value:
        raise ValueError("Only pending_review drafts can be approved")
    d.status = models.DraftStatus.APPROVED.value
    d.updated_at = datetime.utcnow()
    d.expires_at = d.created_at + APPROVED_TTL_FROM_CREATION
    db.add(
        models.AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event="draft.approved",
            details={"draft_id": d.id},
        )
    )
    db.commit()
    db.refresh(d)
    return d


def reject_draft(db: Session, user_id: str, draft_id: str) -> models.Draft:
    d = get_draft(db, user_id, draft_id)
    if not d:
        raise KeyError("draft not found")
    if d.status != models.DraftStatus.PENDING_REVIEW.value:
        raise ValueError("Only pending_review drafts can be rejected")
    d.status = models.DraftStatus.REJECTED.value
    d.updated_at = datetime.utcnow()
    d.expires_at = datetime.utcnow() + REJECTED_RETENTION
    db.add(
        models.AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event="draft.rejected",
            details={"draft_id": d.id},
        )
    )
    db.commit()
    db.refresh(d)
    return d


def delete_draft(db: Session, user_id: str, draft_id: str) -> None:
    """Remove an approved draft before send (discard)."""
    d = get_draft(db, user_id, draft_id)
    if not d:
        raise KeyError("draft not found")
    if d.status != models.DraftStatus.APPROVED.value:
        raise ValueError("Only approved drafts can be discarded before send")
    db.add(
        models.AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event="draft.deleted_before_send",
            details={"draft_id": d.id},
        )
    )
    db.delete(d)
    db.commit()

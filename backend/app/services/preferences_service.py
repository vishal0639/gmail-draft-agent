import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import decrypt_json, encrypt_json
from app.db import models


def get_prefs_dict(db: Session, user_id: str) -> dict:
    p = (
        db.query(models.UserPreferences)
        .filter_by(user_id=user_id)
        .first()
    )
    if not p:
        return {
            "default_tone": "concise",
            "email_signature": "",
        }
    try:
        return decrypt_json(p.enc_data)
    except Exception:
        return {
            "default_tone": "concise",
            "email_signature": "",
        }


def upsert_preferences(db: Session, user_id: str, data: dict) -> dict:
    p = (
        db.query(models.UserPreferences)
        .filter_by(user_id=user_id)
        .first()
    )
    enc = encrypt_json(
        {
            "default_tone": (data.get("default_tone") or "concise").lower(),
            "email_signature": data.get("email_signature") or "",
            "other": data.get("other") or {},
        }
    )
    if p is None:
        p = models.UserPreferences(
            user_id=user_id, enc_data=enc, updated_at=datetime.utcnow()
        )
        db.add(p)
    else:
        p.enc_data = enc
        p.updated_at = datetime.utcnow()
    db.add(
        models.AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event="preferences.updated",
            details={},
        )
    )
    db.commit()
    return get_prefs_dict(db, user_id)

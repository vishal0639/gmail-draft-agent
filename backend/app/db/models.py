import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DraftStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)

    tokens: Mapped["GmailToken | None"] = relationship(
        "GmailToken", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    preferences: Mapped["UserPreferences | None"] = relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    drafts: Mapped[list["Draft"]] = relationship("Draft", back_populates="user")
    send_attempts: Mapped[list["SendAttempt"]] = relationship("SendAttempt", back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")


class OAuthState(Base):
    """CSRF / session binding for OAuth2 redirect."""

    __tablename__ = "oauth_states"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class GmailToken(Base):
    __tablename__ = "gmail_tokens"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # Encrypted refresh token (Fernet)
    enc_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional encrypted access token cache
    enc_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    token_scopes: Mapped[str | None] = mapped_column(Text, nullable=True)  # space-separated, optional
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="tokens")


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # JSON encrypted at app layer before persist (or store encrypted blob of JSON)
    enc_data: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="preferences")


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    thread_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    source_message_id: Mapped[str] = mapped_column(String(128), nullable=False)  # Gmail message id
    in_reply_to_rfc: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Message-ID of parent
    references_rfc: Mapped[str | None] = mapped_column(Text, nullable=True)
    to_addresses: Mapped[str] = mapped_column(Text, default="")  # comma or JSON; keep simple: comma
    subject: Mapped[str] = mapped_column(String(1024), default="")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str] = mapped_column(String(64), default="concise")
    # Store enum .value for SQLite compatibility
    status: Mapped[str] = mapped_column(
        String(32), default=DraftStatus.PENDING_REVIEW.value, index=True
    )
    # Optional: Gmail API draft id if you sync with Gmail
    gmail_draft_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # UTC; pending/approved default lifetime 48h; rejection shortens to 24h from rejection time
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="drafts")
    send_attempts: Mapped[list["SendAttempt"]] = relationship("SendAttempt", back_populates="draft")


class SendAttemptStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class SendAttempt(Base):
    """Idempotent send tracking + result."""

    __tablename__ = "send_attempts"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uq_user_idempotency"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    draft_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("drafts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    gmail_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # errors/response
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="send_attempts")
    draft: Mapped["Draft"] = relationship("Draft", back_populates="send_attempts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    event: Mapped[str] = mapped_column(String(128), index=True)  # draft.created, send.success, etc.
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")

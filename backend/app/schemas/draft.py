import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ToneKind(str, enum.Enum):
    FORMAL = "formal"
    CONCISE = "concise"
    FRIENDLY = "friendly"


class DraftGenerateRequest(BaseModel):
    source_message_id: str = Field(..., description="Gmail message id to reply to")
    tone: ToneKind = ToneKind.CONCISE
    custom_instructions: str | None = Field(
        default=None, description="Optional extra instructions for the draft generator"
    )


class DraftOut(BaseModel):
    id: str
    user_id: str
    thread_id: str | None
    source_message_id: str
    subject: str
    body: str
    tone: str
    status: str
    gmail_draft_id: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DraftUpdateRequest(BaseModel):
    body: str = Field(..., min_length=1)
    subject: str | None = None


class DraftListResponse(BaseModel):
    items: list[DraftOut]
    total: int

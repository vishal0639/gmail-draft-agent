from pydantic import BaseModel, Field


class EmailListQuery(BaseModel):
    filter: str = Field(
        default="unread",
        description="unread | recent | all",
    )
    max_results: int = Field(default=20, ge=1, le=100)


class EmailItem(BaseModel):
    id: str
    thread_id: str | None
    subject: str | None
    from_addr: str | None
    snippet: str | None
    internal_date: str | None
    label_ids: list[str] = Field(default_factory=list)


class EmailListResponse(BaseModel):
    items: list[EmailItem]
    result_size_estimate: int | None = None
    next_page_token: str | None = None


class EmailDetailResponse(EmailItem):
    body_text: str | None
    body_html: str | None
    message_id_rfc: str | None
    in_reply_to: str | None
    references: str | None
    to_addresses: str | None

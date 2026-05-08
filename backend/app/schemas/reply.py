from pydantic import BaseModel, Field


class SendReplyRequest(BaseModel):
    draft_id: str = Field(..., description="Must be in approved state")

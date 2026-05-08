from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str = Field(..., examples=["ok"])


class HealthResponse(BaseModel):
    status: str
    app: str

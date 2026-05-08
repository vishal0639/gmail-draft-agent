from pydantic import BaseModel, Field


class UserPreferencesIn(BaseModel):
    default_tone: str = Field(default="concise", description="formal | concise | friendly")
    email_signature: str = Field(
        default="",
        max_length=8000,
        description="Appended to mock drafts; stored encrypted at rest",
    )
    other: dict | None = None


class UserPreferencesOut(UserPreferencesIn):
    pass

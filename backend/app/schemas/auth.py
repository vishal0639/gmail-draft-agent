from pydantic import BaseModel, Field


class GoogleAuthUrlResponse(BaseModel):
    url: str = Field(..., description="Open this URL in a browser to complete Google OAuth2")
    state: str = Field(..., description="CSRF state (also stored server-side)")

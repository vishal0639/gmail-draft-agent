from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Draftly Gmail AI Reply Agent"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "*"

    database_url: str = "sqlite:///./draftly.db"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://127.0.0.1:8000/api/v1/auth/google/callback"
    # Frontend origin for OAuth: postMessage target + /oauth-done and /oauth-cancel routes
    frontend_oauth_success_url: str = "http://localhost:3000"
    # Read, compose local drafts, send, and allow modifying labels/threading as needed
    google_scopes: str = (
        "openid "
        "https://www.googleapis.com/auth/userinfo.email "
        "https://www.googleapis.com/auth/gmail.readonly "
        "https://www.googleapis.com/auth/gmail.send "
        "https://www.googleapis.com/auth/gmail.compose"
    )

    master_encryption_key: str = Field(
        default="",
        description="Fernet key (base64) for encrypting tokens and preferences at rest",
    )

    # Reply drafts — OpenAI Chat Completions (optional; if unset, mock generator is used)
    openai_api_key: str = Field(default="", description="API key for generating reply drafts")
    openai_model: str = Field(default="gpt-4o-mini", description="Chat model for drafts")

    @property
    def scope_list(self) -> list[str]:
        return [s for s in self.google_scopes.split() if s]

    @field_validator("cors_origins")
    @classmethod
    def split_origins(cls, v: str) -> str:
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()

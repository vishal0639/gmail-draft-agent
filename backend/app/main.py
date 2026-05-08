from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1 import api_router
from app.core.config import get_settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> Any:
    init_db()
    yield


def create_app() -> FastAPI:
    s = get_settings()
    application = FastAPI(
        title=s.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    if s.cors_origins.strip() == "*":
        origins = ["*"]
    else:
        origins = [o.strip() for o in s.cors_origins.split(",") if o.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=s.api_v1_prefix)

    @application.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "service": s.app_name,
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "api": s.api_v1_prefix,
        }

    # Some stacks use "/swagger"; FastAPI’s Swagger UI is at "/docs" by default
    @application.get("/swagger", include_in_schema=False)
    @application.get("/swagger/", include_in_schema=False)
    def redirect_swagger() -> RedirectResponse:
        return RedirectResponse(url="/docs", status_code=307)

    return application


app = create_app()

from fastapi import APIRouter

from app.api.v1 import auth, drafts, emails, health, logs, preferences, replies

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
api_router.include_router(drafts.router, prefix="/drafts", tags=["drafts"])
api_router.include_router(replies.router, prefix="/replies", tags=["replies"])
api_router.include_router(preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])

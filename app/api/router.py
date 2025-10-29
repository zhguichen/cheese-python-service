"""API 路由聚合"""

from fastapi import APIRouter

from app.api.endpoints import practice_router

api_router = APIRouter()
api_router.include_router(practice_router)

__all__ = ["api_router"]

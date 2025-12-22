"""API router configuration."""
from fastapi import APIRouter

from app.api.endpoints import courses, practice, external

api_router = APIRouter()

api_router.include_router(courses.router)
api_router.include_router(practice.router)
api_router.include_router(external.router)


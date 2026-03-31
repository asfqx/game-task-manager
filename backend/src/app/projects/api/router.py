from fastapi import APIRouter

from .v1 import v1_router


projects_router = APIRouter(prefix="/api")
projects_router.include_router(v1_router)

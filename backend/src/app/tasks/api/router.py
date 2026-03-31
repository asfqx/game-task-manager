from fastapi import APIRouter

from .v1 import v1_router


tasks_router = APIRouter(prefix="/api")
tasks_router.include_router(v1_router)

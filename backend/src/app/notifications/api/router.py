from fastapi import APIRouter

from .v1 import v1_router


notifications_router = APIRouter(prefix="/api")
notifications_router.include_router(v1_router)

from fastapi import APIRouter

from .v1 import v1_router


teams_router = APIRouter(prefix="/api")
teams_router.include_router(v1_router)

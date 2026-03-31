from fastapi import APIRouter

from .v1 import v1_router


system_logging_router = APIRouter(prefix="/api")
system_logging_router.include_router(v1_router)

from fastapi import APIRouter

from .v1 import v1_router


lvls_router = APIRouter(prefix="/api")
lvls_router.include_router(v1_router)

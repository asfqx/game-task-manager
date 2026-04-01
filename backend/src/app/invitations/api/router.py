from fastapi import APIRouter

from .v1.router import v1_router


invitations_router = APIRouter(prefix="/api")
invitations_router.include_router(v1_router)

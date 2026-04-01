from fastapi import APIRouter

from .endpoints.invitations import router as invitations_router


v1_router = APIRouter(prefix="/v1/invitations", tags=["Invitations"])
v1_router.include_router(invitations_router)

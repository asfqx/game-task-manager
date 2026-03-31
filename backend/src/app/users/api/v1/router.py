from fastapi import APIRouter

from .endpoints import user_router


v1_router = APIRouter(prefix="/v1/users", tags=["Users"])
v1_router.include_router(user_router)

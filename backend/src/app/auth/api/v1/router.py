from fastapi import APIRouter

from .endpoints import (
    auth_enpoint_router,
    password_reset_router,
    refresh_endpoint_router,
    email_confirm_router,
)


v1_router = APIRouter(prefix="/v1/auth", tags=["Auth"])


v1_router.include_router(
    auth_enpoint_router,
)

v1_router.include_router(
    password_reset_router,
)

v1_router.include_router(
    refresh_endpoint_router,
)

v1_router.include_router(
    email_confirm_router,
)

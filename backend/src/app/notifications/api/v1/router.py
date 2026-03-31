from fastapi import APIRouter

from .endpoints import notification_router


v1_router = APIRouter(prefix="/v1/notifications", tags=["Notifications"])
v1_router.include_router(notification_router)

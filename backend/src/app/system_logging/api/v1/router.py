from fastapi import APIRouter

from .endpoints import user_action_logs_router, xp_logs_router


v1_router = APIRouter(prefix="/v1/system-logging", tags=["System logging"])
v1_router.include_router(xp_logs_router)
v1_router.include_router(user_action_logs_router)

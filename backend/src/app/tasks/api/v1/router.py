from fastapi import APIRouter

from .endpoints import task_router


v1_router = APIRouter(prefix="/v1/tasks", tags=["Tasks"])
v1_router.include_router(task_router)

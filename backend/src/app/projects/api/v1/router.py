from fastapi import APIRouter

from .endpoints import project_router


v1_router = APIRouter(prefix="/v1/projects", tags=["Projects"])
v1_router.include_router(project_router)

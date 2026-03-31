from fastapi import APIRouter

from .endpoints import team_router


v1_router = APIRouter(prefix="/v1/teams", tags=["Teams"])
v1_router.include_router(team_router)

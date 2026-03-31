from fastapi import APIRouter

from .endpoints import lvl_router


v1_router = APIRouter(prefix="/v1/lvls", tags=["Lvls"])
v1_router.include_router(lvl_router)

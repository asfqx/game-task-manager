from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

from app.adapters.s3 import s3_adapter
from app.auth.api import auth_router
from app.core import AsyncSessionLocal, settings
from app.constant import AVATARS_BUCKET, AI_MODELS
from app.invitations.api import invitations_router
from app.lvls.api import lvls_router
from app.lvls.service import LvlService
from app.notifications.api import notifications_router
from app.projects.api import projects_router
from app.system_logging.api import system_logging_router
from app.tasks.api import tasks_router
from app.teams.api import teams_router
from app.users.api import users_router
from app.mock import bootstrap_mock_data



@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        s3_adapter.create_bucket(AVATARS_BUCKET)
        s3_adapter.create_bucket(AI_MODELS)
    except Exception as exc:
        logger.warning(
            "S3 bucket initialization skipped: {}",
            exc,
        )

    async with AsyncSessionLocal() as session:
        await LvlService.create_default_lvls(session)

    await bootstrap_mock_data()

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(lvls_router)
    app.include_router(projects_router)
    app.include_router(teams_router)
    app.include_router(tasks_router)
    app.include_router(notifications_router)
    app.include_router(invitations_router)
    app.include_router(system_logging_router)

    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_title,
    description=settings.app_description,
)

Instrumentator().instrument(app).expose(app, tags=["Metrics"])

origins = [
    "http://localhost:5173",
    "https://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, status

from app.core import DBSession
from app.tasks.filter import TaskFilterDepends
from app.tasks.schema import CreateTaskRequest, RejectTaskRequest, TaskResponse, UpdateTaskRequest
from app.tasks.service import TaskService
from app.users.dependency import AuthenticatedActiveUser


router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[TaskResponse],
    summary="Получить доступные задачи",
)
async def get_tasks(
    user: AuthenticatedActiveUser,
    filters: TaskFilterDepends,
    session: DBSession,
) -> list[TaskResponse]:

    return TaskService.to_task_responses(
        await TaskService.get_tasks(
            current_user=user,
            filters=filters,
            session=session,
        )
    )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskResponse,
    summary="Создать задачу",
)
async def create_task(
    data: CreateTaskRequest,
    user: AuthenticatedActiveUser,
    background_tasks: BackgroundTasks,
    session: DBSession,
) -> TaskResponse:

    task = await TaskService.create_task(
        data=data,
        current_user=user,
        session=session,
        background_tasks=background_tasks,
    )

    return task


@router.get(
    "/{task_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponse,
    summary="Получить задачу по UUID",
)
async def get_task_by_uuid(
    task_uuid: UUID,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> TaskResponse:

    return await TaskService.get_task_by_id(
        task_uuid=task_uuid,
        current_user=user,
        session=session,
    )


@router.patch(
    "/{task_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponse,
    summary="Изменить задачу",
)
async def update_task(
    task_uuid: UUID,
    data: UpdateTaskRequest,
    user: AuthenticatedActiveUser,
    background_tasks: BackgroundTasks,
    session: DBSession,
) -> TaskResponse:

    return await TaskService.update_task(
        task_uuid=task_uuid,
        data=data,
        current_user=user,
        session=session,
        background_tasks=background_tasks,
    )


@router.post(
    "/{task_uuid}/accept",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponse,
    summary="Принять задачу в работу",
)
async def accept_task(
    task_uuid: UUID,
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> TaskResponse:

    return await TaskService.accept_task(
        task_uuid=task_uuid,
        current_user=user,
        session=session,
    )


@router.post(
    "/{task_uuid}/submit-for-review",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponse,
    summary="Отправить задачу на проверку",
)
async def submit_task_for_review(
    task_uuid: UUID,
    user: AuthenticatedActiveUser,
    background_tasks: BackgroundTasks,
    session: DBSession,
) -> TaskResponse:

    task = await TaskService.submit_for_review(
        task_uuid=task_uuid,
        current_user=user,
        session=session,
        background_tasks=background_tasks,
    )

    return task


@router.post(
    "/{task_uuid}/approve",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponse,
    summary="Подтвердить выполнение задачи",
)
async def approve_task(
    task_uuid: UUID,
    user: AuthenticatedActiveUser,
    background_tasks: BackgroundTasks,
    session: DBSession,
) -> TaskResponse:

    task = await TaskService.approve_task(
        task_uuid=task_uuid,
        current_user=user,
        session=session,
        background_tasks=background_tasks,
    )

    return task


@router.post(
    "/{task_uuid}/reject",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponse,
    summary="Отклонить задачу с комментарием",
)
async def reject_task(
    task_uuid: UUID,
    data: RejectTaskRequest,
    user: AuthenticatedActiveUser,
    background_tasks: BackgroundTasks,
    session: DBSession,
) -> TaskResponse:

    task = await TaskService.reject_task(
        task_uuid=task_uuid,
        data=data,
        current_user=user,
        session=session,
        background_tasks=background_tasks,
    )

    return task

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, status

from app.core import DBSession
from app.invitations.schema import CreateInvitationRequest, InvitationResponse
from app.invitations.service import InvitationService
from app.users.dependency import AuthenticatedActiveUser


router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[InvitationResponse],
    summary="Получить список приглашений",
)
async def get_invitations(
    user: AuthenticatedActiveUser,
    session: DBSession,
) -> list[InvitationResponse]:

    return await InvitationService.get_invitations(
        current_user=user,
        session=session,
    )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=InvitationResponse,
    summary="Отправить приглашение в проект",
)
async def create_invitation(
    data: CreateInvitationRequest,
    user: AuthenticatedActiveUser,
    background_tasks: BackgroundTasks,
    session: DBSession,
) -> InvitationResponse:

    return await InvitationService.create_invitation(
        data=data,
        current_user=user,
        session=session,
        background_tasks=background_tasks,
    )


@router.post(
    "/{invitation_uuid}/accept",
    status_code=status.HTTP_200_OK,
    response_model=InvitationResponse,
    summary="Принять приглашение",
)
async def accept_invitation(
    invitation_uuid: UUID,
    user: AuthenticatedActiveUser,
    background_tasks: BackgroundTasks,
    session: DBSession,
) -> InvitationResponse:

    return await InvitationService.accept_invitation(
        invitation_uuid=invitation_uuid,
        current_user=user,
        session=session,
        background_tasks=background_tasks,
    )


@router.post(
    "/{invitation_uuid}/reject",
    status_code=status.HTTP_200_OK,
    response_model=InvitationResponse,
    summary="Отклонить приглашение",
)
async def reject_invitation(
    invitation_uuid: UUID,
    user: AuthenticatedActiveUser,
    background_tasks: BackgroundTasks,
    session: DBSession,
) -> InvitationResponse:

    return await InvitationService.reject_invitation(
        invitation_uuid=invitation_uuid,
        current_user=user,
        session=session,
        background_tasks=background_tasks,
    )

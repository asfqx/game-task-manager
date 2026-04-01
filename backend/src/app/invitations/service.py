from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enum import InvitationStatus, UserRole
from app.error_handler import handle_connection_errors, handle_model_errors
from app.invitations.model import Invitation
from app.invitations.repository import InvitationRepository
from app.invitations.schema import (
    CreateInvitationRequest,
    InvitationProjectResponse,
    InvitationResponse,
    InvitationTeamResponse,
)
from app.lvls.service import LvlService
from app.notifications.service import NotificationService
from app.system_logging.service import SystemLoggingService
from app.teams.model import TeamMember
from app.teams.repository import TeamRepository
from app.users.model import User
from app.users.repository import UserRepository
from app.users.schema import UserShortResponse


class InvitationService:

    @staticmethod
    def _to_user_short(user: User | None) -> UserShortResponse | None:
        if user is None:
            return None

        return UserShortResponse(
            uuid=user.uuid,
            username=user.username,
            fio=user.fio,
        )

    @classmethod
    def _to_response(cls, invitation: Invitation) -> InvitationResponse:

        return InvitationResponse(
            uuid=invitation.uuid,
            project_uuid=invitation.project_uuid,
            project=InvitationProjectResponse(
                uuid=invitation.project.uuid,
                title=invitation.project.title,
            ),
            team_uuid=invitation.team_uuid,
            team=InvitationTeamResponse(
                uuid=invitation.team.uuid,
                name=invitation.team.name,
                project_uuid=invitation.team.project_uuid,
                project_title=invitation.team.project.title,
            ),
            sender_user_uuid=invitation.sender_user_uuid,
            sender_user=cls._to_user_short(invitation.sender_user),
            recipient_user_uuid=invitation.recipient_user_uuid,
            recipient_user=cls._to_user_short(invitation.recipient_user),
            recipient_login=invitation.recipient_login,
            status=invitation.status,
            created_at=invitation.created_at,
            updated_at=invitation.updated_at,
            resolved_at=invitation.resolved_at,
        )

    @staticmethod
    def _can_manage_team_invitations(team, current_user: User) -> bool:

        # Владелец проекта может приглашать в любую команду проекта,
        # тимлид — только в ту команду, которую он возглавляет.
        return (
            current_user.role == UserRole.ADMIN
            or team.project.creator_uuid == current_user.uuid
            or team.lead_uuid == current_user.uuid
        )

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_invitations(
        cls,
        current_user: User,
        session: AsyncSession,
    ) -> list[InvitationResponse]:

        invitations = await InvitationRepository.get_related_for_user(current_user.uuid, session)
        return [cls._to_response(invitation) for invitation in invitations]

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def create_invitation(
        cls,
        data: CreateInvitationRequest,
        current_user: User,
        session: AsyncSession,
        background_tasks: BackgroundTasks | None = None,
    ) -> InvitationResponse:

        team = await TeamRepository.get(data.team_uuid, session)
        if team is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Команда не найдена")

        if not cls._can_manage_team_invitations(team, current_user):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для отправки приглашения в команду",
            )

        recipient_login = data.recipient_login.strip()
        recipient_user = await UserRepository.get_by_login(recipient_login, session)
        if recipient_user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        if recipient_user.uuid == current_user.uuid:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Нельзя пригласить самого себя")

        existing_membership = await TeamRepository.get_membership(team.uuid, recipient_user.uuid, session)
        if existing_membership is not None or team.lead_uuid == recipient_user.uuid:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Пользователь уже состоит в команде")

        waiting_invitation = await InvitationRepository.get_pending_by_team_and_recipient(
            team.uuid,
            recipient_user.uuid,
            session,
        )
        if waiting_invitation is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Приглашение уже ожидает ответа")

        invitation = await InvitationRepository.create(
            Invitation(
                team_uuid=team.uuid,
                project_uuid=team.project_uuid,
                sender_user_uuid=current_user.uuid,
                recipient_user_uuid=recipient_user.uuid,
                recipient_login=recipient_login,
                status=InvitationStatus.WAITING,
            ),
            session,
        )

        await SystemLoggingService.log_user_action(
            session,
            action="team_invitation_created",
            actor_user_uuid=current_user.uuid,
            entity_type="invitation",
            entity_uuid=invitation.uuid,
            details={
                "team_uuid": str(team.uuid),
                "project_uuid": str(team.project_uuid),
                "recipient_user_uuid": str(recipient_user.uuid),
            },
            commit=False,
        )
        await session.commit()

        NotificationService.schedule(
            background_tasks,
            recipient_user_uuids=[recipient_user.uuid],
            sender_user_uuid=current_user.uuid,
            content=f'Вас пригласили в команду "{team.name}" проекта "{team.project.title}"',
        )

        return cls._to_response(invitation)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def accept_invitation(
        cls,
        invitation_uuid: UUID,
        current_user: User,
        session: AsyncSession,
        background_tasks: BackgroundTasks | None = None,
    ) -> InvitationResponse:

        invitation = await InvitationRepository.get(invitation_uuid, session)
        if invitation is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Приглашение не найдено")

        if invitation.recipient_user_uuid != current_user.uuid:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для принятия приглашения",
            )

        if invitation.status != InvitationStatus.WAITING:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Приглашение уже обработано")

        existing_membership = await TeamRepository.get_membership(invitation.team_uuid, current_user.uuid, session)
        if existing_membership is None and invitation.team.lead_uuid != current_user.uuid:
            entry_lvl = await LvlService.get_entry_level(session)
            await TeamRepository.create_membership(
                TeamMember(
                    team_uuid=invitation.team_uuid,
                    user_uuid=current_user.uuid,
                    added_by_uuid=invitation.sender_user_uuid,
                    lvl_uuid=entry_lvl.uuid if entry_lvl else None,
                ),
                session,
            )

        invitation = await InvitationRepository.update_status(invitation, InvitationStatus.ACCEPTED, session)

        await SystemLoggingService.log_user_action(
            session,
            action="team_invitation_accepted",
            actor_user_uuid=current_user.uuid,
            entity_type="invitation",
            entity_uuid=invitation.uuid,
            details={
                "team_uuid": str(invitation.team_uuid),
                "project_uuid": str(invitation.project_uuid),
            },
            commit=False,
        )
        await session.commit()

        if invitation.sender_user_uuid is not None:
            NotificationService.schedule(
                background_tasks,
                recipient_user_uuids=[invitation.sender_user_uuid],
                sender_user_uuid=current_user.uuid,
                content=f'{current_user.fio} принял(а) приглашение в команду "{invitation.team.name}"',
            )

        return cls._to_response(invitation)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def reject_invitation(
        cls,
        invitation_uuid: UUID,
        current_user: User,
        session: AsyncSession,
        background_tasks: BackgroundTasks | None = None,
    ) -> InvitationResponse:

        invitation = await InvitationRepository.get(invitation_uuid, session)
        if invitation is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Приглашение не найдено")

        if invitation.recipient_user_uuid != current_user.uuid:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для отклонения приглашения",
            )

        if invitation.status != InvitationStatus.WAITING:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Приглашение уже обработано")

        invitation = await InvitationRepository.update_status(invitation, InvitationStatus.REJECTED, session)

        await SystemLoggingService.log_user_action(
            session,
            action="team_invitation_rejected",
            actor_user_uuid=current_user.uuid,
            entity_type="invitation",
            entity_uuid=invitation.uuid,
            details={
                "team_uuid": str(invitation.team_uuid),
                "project_uuid": str(invitation.project_uuid),
            },
            commit=False,
        )
        await session.commit()

        if invitation.sender_user_uuid is not None:
            NotificationService.schedule(
                background_tasks,
                recipient_user_uuids=[invitation.sender_user_uuid],
                sender_user_uuid=current_user.uuid,
                content=f'{current_user.fio} отклонил(а) приглашение в команду "{invitation.team.name}"',
            )

        return cls._to_response(invitation)

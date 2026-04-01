import datetime as dt
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enum import InvitationStatus
from app.invitations.model import Invitation
from app.teams.model import Team


INVITATION_LOAD_OPTIONS = (
    selectinload(Invitation.team).selectinload(Team.project),
    selectinload(Invitation.project),
    selectinload(Invitation.sender_user),
    selectinload(Invitation.recipient_user),
)


class InvitationRepository:

    @staticmethod
    async def get(
        invitation_uuid: UUID,
        session: AsyncSession,
    ) -> Invitation | None:

        stmt = (
            select(Invitation)
            .options(*INVITATION_LOAD_OPTIONS)
            .where(Invitation.uuid == invitation_uuid)
        )
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_related_for_user(
        user_uuid: UUID,
        session: AsyncSession,
    ) -> Sequence[Invitation]:

        stmt = (
            select(Invitation)
            .options(*INVITATION_LOAD_OPTIONS)
            .where(
                or_(
                    Invitation.sender_user_uuid == user_uuid,
                    Invitation.recipient_user_uuid == user_uuid,
                )
            )
            .order_by(Invitation.created_at.desc(), Invitation.uuid.desc())
        )
        result = await session.execute(stmt)

        return result.scalars().all()

    @staticmethod
    async def get_pending_by_team_and_recipient(
        team_uuid: UUID,
        recipient_user_uuid: UUID,
        session: AsyncSession,
    ) -> Invitation | None:

        stmt = (
            select(Invitation)
            .options(*INVITATION_LOAD_OPTIONS)
            .where(
                Invitation.team_uuid == team_uuid,
                Invitation.recipient_user_uuid == recipient_user_uuid,
                Invitation.status == InvitationStatus.WAITING,
            )
        )
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        invitation: Invitation,
        session: AsyncSession,
    ) -> Invitation:

        session.add(invitation)
        await session.commit()

        refreshed = await InvitationRepository.get(invitation.uuid, session)
        return refreshed  # type: ignore[return-value]

    @staticmethod
    async def update_status(
        invitation: Invitation,
        status: InvitationStatus,
        session: AsyncSession,
    ) -> Invitation:

        invitation.status = status
        invitation.resolved_at = dt.datetime.now(dt.UTC)
        await session.commit()

        refreshed = await InvitationRepository.get(invitation.uuid, session)
        return refreshed  # type: ignore[return-value]

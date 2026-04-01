from datetime import timedelta
from typing import Sequence
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.s3 import s3_adapter
from app.constant import AVATARS_BUCKET
from app.enum import UserRole
from app.error_handler import handle_connection_errors, handle_model_errors
from app.system_logging.service import SystemLoggingService
from app.tasks.repository import TaskRepository
from app.teams.repository import TeamRepository
from app.users.filter import UserFilterQueryParams
from app.users.model import User
from app.users.repository import UserRepository
from app.users.schema import (
    CreatePreSignedURLResponse,
    UpdateUserProfileRequest,
    UpdateUserProfileResponse,
    UserShortResponse,
)


class UserService:

    @classmethod
    async def _build_user_profile_payload(
        cls,
        target_user: User,
        viewer: User,
        session: AsyncSession,
    ) -> dict:

        teams = await TeamRepository.get_by_user(target_user.uuid, session)
        completed_tasks = await TaskRepository.get_completed_by_assignee(target_user.uuid, session)
        visible_teams: list[dict] = []

        for team in teams:
            if (
                viewer.role != UserRole.ADMIN
                and viewer.uuid != target_user.uuid
                and team.project.creator_uuid != viewer.uuid
                and team.lead_uuid != viewer.uuid
                and False
            ):
                continue

            membership = next(
                (member for member in team.members if member.user_uuid == target_user.uuid),
                None,
            )
            if membership is None or membership.lvl is None:
                continue

            visible_teams.append(
                {
                    "team_uuid": team.uuid,
                    "team_name": team.name,
                    "project_uuid": team.project_uuid,
                    "project_title": team.project.title,
                    "is_team_lead": team.lead_uuid == target_user.uuid,
                    "xp_amount": membership.xp_amount,
                    "lvl_uuid": membership.lvl_uuid,
                    "lvl": membership.lvl,
                }
            )

        visible_teams.sort(key=lambda team: (team["project_title"].lower(), team["team_name"].lower()))

        return {
            "uuid": target_user.uuid,
            "email": target_user.email,
            "username": target_user.username,
            "fio": target_user.fio,
            "role": target_user.role,
            "status": target_user.status,
            "gender": target_user.gender,
            "email_confirmed": target_user.email_confirmed,
            "avatar_url": target_user.avatar_url,
            "telegram": target_user.telegram,
            "phone_number": target_user.phone_number,
            "created_at": target_user.created_at,
            "updated_at": target_user.updated_at,
            "last_login_at": target_user.last_login_at,
            "teams": visible_teams,
            "completed_tasks": [
                {
                    "task_uuid": task.uuid,
                    "title": task.title,
                    "team_uuid": task.team_uuid,
                    "team_name": task.team.name,
                    "project_uuid": task.team.project_uuid,
                    "project_title": task.team.project.title,
                    "xp_amount": task.xp_amount,
                    "completed_at": task.completed_at,
                }
                for task in completed_tasks
            ],
        }

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_user_profile(
        cls,
        current_user: User,
        session: AsyncSession,
    ) -> dict:

        exist_user = await UserRepository.get(current_user.uuid, session)
        if not exist_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        return await cls._build_user_profile_payload(exist_user, current_user, session)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_user_by_id(
        cls,
        user_uuid: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> dict:

        exist_user = await UserRepository.get(user_uuid, session)
        if not exist_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        return await cls._build_user_profile_payload(exist_user, current_user, session)

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_all(
        cls,
        current_user: User,
        filters: UserFilterQueryParams,
        session: AsyncSession,
    ) -> Sequence[dict]:

        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра пользователей",
            )

        users = await UserRepository.get_all(filters, session)
        if not users:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователи не найдены")

        return [
            await cls._build_user_profile_payload(user, current_user, session)
            for user in users
        ]

    @classmethod
    @handle_model_errors
    @handle_connection_errors
    async def get_directory(
        cls,
        current_user: User,
        session: AsyncSession,
        query: str | None = None,
        limit: int = 20,
    ) -> Sequence[User]:

        return await UserRepository.get_directory(
            query=query,
            limit=limit,
            session=session,
        )

    @staticmethod
    @handle_model_errors
    @handle_connection_errors
    async def delete(
        current_user: User,
        user_uuid: UUID,
        session: AsyncSession,
    ) -> None:

        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для блокировки пользователя")
        if current_user.uuid == user_uuid:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить самого себя")

        exist_user = await UserRepository.get(user_uuid, session)
        if not exist_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        await UserRepository.ban(exist_user, session)
        await SystemLoggingService.log_user_action(
            session,
            action="user_banned",
            actor_user_uuid=current_user.uuid,
            entity_type="user",
            entity_uuid=exist_user.uuid,
            details={"target_user_uuid": str(exist_user.uuid)},
        )

    @staticmethod
    @handle_model_errors
    @handle_connection_errors
    async def unban(
        current_user: User,
        user_uuid: UUID,
        session: AsyncSession,
    ) -> None:

        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для разблокировки пользователя")
        if current_user.uuid == user_uuid:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Нельзя изменить статус самого себя")

        exist_user = await UserRepository.get(user_uuid, session)
        if not exist_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        await UserRepository.unban(exist_user, session)
        await SystemLoggingService.log_user_action(
            session,
            action="user_unbanned",
            actor_user_uuid=current_user.uuid,
            entity_type="user",
            entity_uuid=exist_user.uuid,
            details={"target_user_uuid": str(exist_user.uuid)},
        )

    @staticmethod
    @handle_model_errors
    @handle_connection_errors
    async def update_bio(
        new_bio: UpdateUserProfileRequest,
        current_user: User,
        session: AsyncSession,
    ) -> UpdateUserProfileResponse:

        exist_user = await UserRepository.get(current_user.uuid, session)
        if not exist_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        if new_bio.email:
            normalized_email = new_bio.email.lower()
            if normalized_email != exist_user.email:
                user_with_same_email = await UserRepository.get_by_login(normalized_email, session)
                if user_with_same_email and user_with_same_email.uuid != exist_user.uuid:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже существует")
                new_bio.email = normalized_email

        if new_bio.avatar_url and not s3_adapter.is_exists(AVATARS_BUCKET, new_bio.avatar_url):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Передан некорректный avatar_url")

        updated_data = await UserRepository.update(exist_user, new_bio, session)
        await SystemLoggingService.log_user_action(
            session,
            action="profile_updated",
            actor_user_uuid=exist_user.uuid,
            entity_type="user",
            entity_uuid=exist_user.uuid,
            details={"changed_fields": sorted(new_bio.model_dump(exclude_unset=True).keys())},
        )

        return UpdateUserProfileResponse(
            username=updated_data.username,
            email=updated_data.email,
            fio=updated_data.fio,
            avatar_url=updated_data.avatar_url,
            telegram=updated_data.telegram,
            phone_number=updated_data.phone_number,
        )

    @staticmethod
    @handle_model_errors
    @handle_connection_errors
    async def upload_avatar(
        user: User,
    ) -> CreatePreSignedURLResponse:

        url = s3_adapter.get_presigned_url(
            bucket_name=AVATARS_BUCKET,
            object_name=f"{user.uuid}/{uuid4()}.png",
            expires=timedelta(minutes=15),
        )

        return CreatePreSignedURLResponse(upload_url=url)

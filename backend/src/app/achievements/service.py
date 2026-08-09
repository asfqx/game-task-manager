import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.achievements.model import UserAchievement
from app.achievements.repository import UserAchievementRepository
from app.achievements.schema import AchievementResponse
from app.enum import TaskStatus
from app.lvls.service import LvlService
from app.system_logging.model import UserActionLog, XpAccrualLog
from app.system_logging.repository import XpAccrualLogRepository
from app.tasks.model import Task
from app.tasks.repository import TASK_LOAD_OPTIONS, TaskRepository
from app.teams.model import Team, TeamMember
from app.teams.repository import TeamRepository


@dataclass(frozen=True)
class AchievementDefinition:

    key: str
    title: str
    description: str
    condition: str
    icon: str
    target: int
    xp_reward: int


class AchievementService:

    DEFINITIONS: tuple[AchievementDefinition, ...] = (
        AchievementDefinition("first_done_task", "Первый финиш", "Закрыта первая задача.", "Выполнить 1 задачу", "flag", 1, 20),
        AchievementDefinition("five_done_tasks", "Серийный исполнитель", "Пять завершенных задач делают прогресс заметным.", "Выполнить 5 задач", "check-circle", 5, 40),
        AchievementDefinition("xp_collector", "Охотник за XP", "Накоплена первая тысяча XP по всем командам.", "Набрать 1000 XP", "sparkles", 1000, 60),
        AchievementDefinition("team_player", "Командный игрок", "Участие в нескольких командах помогает видеть проект шире.", "Состоять в 3 командах", "users", 3, 50),
        AchievementDefinition("level_three", "Восходящая звезда", "Достигнут третий уровень хотя бы в одной команде.", "Получить 3 уровень", "star", 3, 70),
        AchievementDefinition("clean_fifteen", "Без возвратов", "Пятнадцать задач закрыты без возврата на доработку.", "15 задач без доработки", "shield", 15, 120),
        AchievementDefinition("daily_streak_ten", "Ровный темп", "Задачи выполнялись каждый день десять дней подряд.", "10 дней подряд с задачами", "calendar", 10, 100),
        AchievementDefinition("team_sprint", "Командный спринт", "Команда закрыла плотный недельный спринт.", "5 задач команды за 7 дней", "zap", 5, 80),
        AchievementDefinition("deadline_runner", "До дедлайна", "Пять задач завершены не позже дедлайна.", "5 задач в срок", "timer", 5, 60),
        AchievementDefinition("review_ready", "С первого захода", "Пять задач прошли через проверку и были закрыты.", "5 задач через проверку", "eye", 5, 50),
        AchievementDefinition("high_value_closer", "Крупная добыча", "Закрыты задачи на две тысячи XP суммарно.", "2000 XP за задачи", "gem", 2000, 100),
        AchievementDefinition("fast_week", "Ударная неделя", "За семь дней закрыто семь задач.", "7 задач за 7 дней", "flame", 7, 75),
        AchievementDefinition("consistent_month", "Рабочий ритм", "Задачи закрывались в пятнадцать разных дней.", "15 активных дней", "pulse", 15, 120),
        AchievementDefinition("task_marathon", "Марафонец", "Тридцать выполненных задач в профиле.", "Выполнить 30 задач", "route", 30, 150),
        AchievementDefinition("level_five", "Мастер уровня", "Достигнут пятый уровень хотя бы в одной команде.", "Получить 5 уровень", "crown", 5, 120),
    )

    @staticmethod
    def _get_task_unlock_date(completed_tasks: Sequence[Task], target: int) -> dt.datetime | None:
        dated_tasks = sorted(
            (task for task in completed_tasks if task.completed_at is not None),
            key=lambda task: task.completed_at,
        )

        if len(dated_tasks) < target:
            return None

        return dated_tasks[target - 1].completed_at

    @staticmethod
    def _get_level_value(team: Team, user_uuid: UUID) -> int:
        membership = next((member for member in team.members if member.user_uuid == user_uuid), None)

        if membership is None or membership.lvl is None:
            return 0

        try:
            return int(membership.lvl.value)
        except ValueError:
            return 0

    @staticmethod
    def _get_completed_dates(tasks: Sequence[Task]) -> list[dt.date]:
        return sorted(
            {
                task.completed_at.date()
                for task in tasks
                if task.completed_at is not None
            },
        )

    @classmethod
    def _get_best_daily_streak(cls, tasks: Sequence[Task]) -> int:
        dates = cls._get_completed_dates(tasks)
        if not dates:
            return 0

        best_streak = 1
        current_streak = 1

        for previous_date, current_date in zip(dates, dates[1:]):
            if current_date == previous_date + dt.timedelta(days=1):
                current_streak += 1
            else:
                current_streak = 1

            best_streak = max(best_streak, current_streak)

        return best_streak

    @staticmethod
    def _get_best_rolling_count(tasks: Sequence[Task], window_days: int) -> int:
        timestamps = sorted(
            task.completed_at
            for task in tasks
            if task.completed_at is not None
        )
        best_count = 0
        left_index = 0

        for right_index, right_time in enumerate(timestamps):
            while right_time - timestamps[left_index] > dt.timedelta(days=window_days):
                left_index += 1

            best_count = max(best_count, right_index - left_index + 1)

        return best_count

    @classmethod
    def _get_team_sprint_progress(cls, teams: Sequence[Team], team_completed_tasks: Sequence[Task]) -> int:
        team_uuids = {team.uuid for team in teams}
        best_count = 0

        for team_uuid in team_uuids:
            team_tasks = [task for task in team_completed_tasks if task.team_uuid == team_uuid]
            best_count = max(best_count, cls._get_best_rolling_count(team_tasks, 7))

        return best_count

    @staticmethod
    async def _get_rejected_task_uuids(session: AsyncSession) -> set[UUID]:
        stmt = select(UserActionLog.entity_uuid).where(
            UserActionLog.action == "task_rejected",
            UserActionLog.entity_type == "task",
            UserActionLog.entity_uuid.is_not(None),
        )
        result = await session.execute(stmt)

        return {task_uuid for task_uuid in result.scalars().all() if task_uuid is not None}

    @staticmethod
    async def _get_completed_tasks_for_teams(
        teams: Sequence[Team],
        session: AsyncSession,
    ) -> Sequence[Task]:
        team_uuids = [team.uuid for team in teams]
        if not team_uuids:
            return []

        stmt = (
            select(Task)
            .options(*TASK_LOAD_OPTIONS)
            .where(
                Task.team_uuid.in_(team_uuids),
                Task.status == TaskStatus.DONE,
            )
            .order_by(Task.completed_at)
        )
        result = await session.execute(stmt)

        return result.scalars().unique().all()

    @staticmethod
    def _select_reward_membership(teams: Sequence[Team], user_uuid: UUID) -> TeamMember | None:
        memberships = [
            member
            for team in teams
            for member in team.members
            if member.user_uuid == user_uuid
        ]
        if not memberships:
            return None

        return max(memberships, key=lambda membership: membership.xp_amount)

    @classmethod
    def build_achievements(
        cls,
        *,
        user_uuid: UUID,
        teams: Sequence[Team],
        completed_tasks: Sequence[Task],
        team_completed_tasks: Sequence[Task],
        rejected_task_uuids: set[UUID],
        unlocked_achievements: Sequence[UserAchievement],
    ) -> list[AchievementResponse]:
        unlocked_by_key = {
            achievement.achievement_key: achievement
            for achievement in unlocked_achievements
        }
        clean_completed_tasks = [
            task for task in completed_tasks
            if task.uuid not in rejected_task_uuids
        ]
        in_time_tasks = [
            task for task in completed_tasks
            if task.completed_at is not None and task.deadline is not None and task.completed_at <= task.deadline
        ]
        reviewed_tasks = [
            task for task in completed_tasks
            if task.submitted_for_review_at is not None
        ]
        total_done_tasks = len(completed_tasks)
        total_task_xp = sum(task.xp_amount for task in completed_tasks)
        total_team_xp = sum(
            member.xp_amount
            for team in teams
            for member in team.members
            if member.user_uuid == user_uuid
        )
        max_level = max((cls._get_level_value(team, user_uuid) for team in teams), default=0)
        team_count = len(teams)
        best_daily_streak = cls._get_best_daily_streak(completed_tasks)
        best_weekly_count = cls._get_best_rolling_count(completed_tasks, 7)
        team_sprint_progress = cls._get_team_sprint_progress(teams, team_completed_tasks)
        active_days = len(cls._get_completed_dates(completed_tasks))

        progress_by_key = {
            "first_done_task": total_done_tasks,
            "five_done_tasks": total_done_tasks,
            "xp_collector": total_team_xp,
            "team_player": team_count,
            "level_three": max_level,
            "clean_fifteen": len(clean_completed_tasks),
            "daily_streak_ten": best_daily_streak,
            "team_sprint": team_sprint_progress,
            "deadline_runner": len(in_time_tasks),
            "review_ready": len(reviewed_tasks),
            "high_value_closer": total_task_xp,
            "fast_week": best_weekly_count,
            "consistent_month": active_days,
            "task_marathon": total_done_tasks,
            "level_five": max_level,
        }
        unlocked_at_by_key = {
            "first_done_task": cls._get_task_unlock_date(completed_tasks, 1),
            "five_done_tasks": cls._get_task_unlock_date(completed_tasks, 5),
            "clean_fifteen": cls._get_task_unlock_date(clean_completed_tasks, 15),
            "task_marathon": cls._get_task_unlock_date(completed_tasks, 30),
        }

        achievements: list[AchievementResponse] = []
        for definition in cls.DEFINITIONS:
            stored_achievement = unlocked_by_key.get(definition.key)
            progress = progress_by_key[definition.key]
            is_unlocked = stored_achievement is not None or progress >= definition.target
            achievements.append(
                AchievementResponse(
                    key=definition.key,
                    title=definition.title,
                    description=definition.description,
                    condition=definition.condition,
                    icon=definition.icon,
                    target=definition.target,
                    progress=min(progress, definition.target),
                    xp_reward=definition.xp_reward,
                    is_unlocked=is_unlocked,
                    unlocked_at=(
                        stored_achievement.unlocked_at
                        if stored_achievement is not None
                        else unlocked_at_by_key.get(definition.key)
                    ),
                ),
            )

        return achievements

    @classmethod
    async def sync_user_achievements(
        cls,
        user_uuid: UUID,
        session: AsyncSession,
        *,
        commit: bool = True,
    ) -> list[AchievementResponse]:
        teams = await TeamRepository.get_by_user(user_uuid, session)
        completed_tasks = await TaskRepository.get_completed_by_assignee(user_uuid, session)
        team_completed_tasks = await cls._get_completed_tasks_for_teams(teams, session)
        rejected_task_uuids = await cls._get_rejected_task_uuids(session)
        unlocked_achievements = await UserAchievementRepository.get_by_user(user_uuid, session)

        achievements = cls.build_achievements(
            user_uuid=user_uuid,
            teams=teams,
            completed_tasks=completed_tasks,
            team_completed_tasks=team_completed_tasks,
            rejected_task_uuids=rejected_task_uuids,
            unlocked_achievements=unlocked_achievements,
        )
        unlocked_keys = {achievement.achievement_key for achievement in unlocked_achievements}
        newly_unlocked = [
            achievement for achievement in achievements
            if achievement.is_unlocked and achievement.key not in unlocked_keys
        ]

        if not newly_unlocked:
            return achievements

        reward_membership = cls._select_reward_membership(teams, user_uuid)
        total_reward = sum(achievement.xp_reward for achievement in newly_unlocked)

        for achievement in newly_unlocked:
            await UserAchievementRepository.create(
                UserAchievement(
                    user_uuid=user_uuid,
                    achievement_key=achievement.key,
                    xp_reward=achievement.xp_reward,
                ),
                session,
            )

        if reward_membership is not None and total_reward > 0:
            reward_membership.xp_amount += total_reward
            await LvlService.assign_level_for_team_member(reward_membership, session)
            await XpAccrualLogRepository.create(
                XpAccrualLog(
                    xp_amount=total_reward,
                    recipient_user_uuid=user_uuid,
                    issuer_user_uuid=None,
                    task_uuid=None,
                ),
                session,
            )

        if commit:
            await session.commit()

        return await cls.sync_user_achievements(user_uuid, session, commit=commit)

    @classmethod
    async def get_user_achievements(
        cls,
        user_uuid: UUID,
        session: AsyncSession,
    ) -> list[AchievementResponse]:

        return await cls.sync_user_achievements(user_uuid, session)

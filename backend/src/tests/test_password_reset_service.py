import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi import HTTPException, status

from app.auth.constant import PASSWORD_RESET_TOKEN_EXPIRE_TIME
from app.auth.services.password_reset import PasswordResetService


class PasswordResetServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_reset_stores_token_schedules_email_and_logs_request(self) -> None:
        cache = Mock()
        cache.set = AsyncMock()
        background = Mock()
        session = Mock()
        user = SimpleNamespace(uuid=uuid4(), username="alice")

        with (
            patch(
                "app.auth.services.password_reset.UserRepository.get_by_login",
                new=AsyncMock(return_value=user),
            ) as get_by_login,
            patch(
                "app.auth.services.password_reset.get_cache_adapter",
                return_value=cache,
            ),
            patch(
                "app.auth.services.password_reset.secrets.token_urlsafe",
                return_value="reset-token",
            ),
            patch(
                "app.auth.services.password_reset.SystemLoggingService.log_user_action",
                new=AsyncMock(),
            ) as log_user_action,
        ):
            await PasswordResetService.reset(
                "Alice@Example.com",
                background,
                session,
            )

        get_by_login.assert_awaited_once_with("alice@example.com", session)
        cache.set.assert_awaited_once_with(
            "password-reset:alice@example.com",
            "reset-token",
            PASSWORD_RESET_TOKEN_EXPIRE_TIME,
        )
        background.add_task.assert_called_once()
        self.assertEqual(background.add_task.call_args.args[1:], (
            "alice@example.com",
            "alice",
            "reset-token",
        ))
        log_user_action.assert_awaited_once_with(
            session,
            action="password_reset_requested",
            actor_user_uuid=user.uuid,
            entity_type="user",
            entity_uuid=user.uuid,
        )

    async def test_reset_does_nothing_for_unknown_email(self) -> None:
        background = Mock()

        with (
            patch(
                "app.auth.services.password_reset.UserRepository.get_by_login",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "app.auth.services.password_reset.get_cache_adapter",
            ) as get_cache_adapter,
            patch(
                "app.auth.services.password_reset.SystemLoggingService.log_user_action",
                new=AsyncMock(),
            ) as log_user_action,
        ):
            await PasswordResetService.reset(
                "missing@example.com",
                background,
                session=Mock(),
            )

        get_cache_adapter.assert_not_called()
        background.add_task.assert_not_called()
        log_user_action.assert_not_awaited()

    async def test_confirm_hashes_new_password_and_updates_user(self) -> None:
        cache = Mock()
        cache.get = AsyncMock(return_value="reset-token")
        session = Mock()
        user = SimpleNamespace(uuid=uuid4())

        with (
            patch(
                "app.auth.services.password_reset.get_cache_adapter",
                return_value=cache,
            ),
            patch(
                "app.auth.services.password_reset.UserRepository.get_by_login",
                new=AsyncMock(return_value=user),
            ) as get_by_login,
            patch(
                "app.auth.services.password_reset.Argon2Hasher.hash",
                return_value="hashed-password",
            ) as hash_password,
            patch(
                "app.auth.services.password_reset.UserRepository.update_password",
                new=AsyncMock(),
            ) as update_password,
            patch(
                "app.auth.services.password_reset.SystemLoggingService.log_user_action",
                new=AsyncMock(),
            ) as log_user_action,
        ):
            await PasswordResetService.confirm(
                "Alice@Example.com",
                "reset-token",
                "new-password",
                session,
            )

        cache.get.assert_awaited_once_with("password-reset:alice@example.com")
        get_by_login.assert_awaited_once_with("alice@example.com", session)
        hash_password.assert_called_once_with("new-password")
        update_password.assert_awaited_once_with(user, "hashed-password", session)
        log_user_action.assert_awaited_once_with(
            session,
            action="password_reset_completed",
            actor_user_uuid=user.uuid,
            entity_type="user",
            entity_uuid=user.uuid,
        )

    async def test_confirm_rejects_missing_token_before_user_lookup(self) -> None:
        cache = Mock()
        cache.get = AsyncMock(return_value=None)

        with (
            patch(
                "app.auth.services.password_reset.get_cache_adapter",
                return_value=cache,
            ),
            patch(
                "app.auth.services.password_reset.UserRepository.get_by_login",
                new=AsyncMock(),
            ) as get_by_login,
        ):
            with self.assertRaises(HTTPException) as error:
                await PasswordResetService.confirm(
                    "alice@example.com",
                    "reset-token",
                    "new-password",
                    session=Mock(),
                )

        self.assertEqual(error.exception.status_code, status.HTTP_400_BAD_REQUEST)
        get_by_login.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()

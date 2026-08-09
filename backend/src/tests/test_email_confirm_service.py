import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi import HTTPException, status

from app.auth.constant import EMAIL_CONFIRM_TOKEN_EXPIRE_TIME
from app.auth.services.email_confirm import EmailConfirmService


class EmailConfirmServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_send_token_stores_token_and_schedules_email(self) -> None:
        cache = Mock()
        cache.set = AsyncMock()
        background = Mock()
        user = SimpleNamespace(
            uuid=uuid4(),
            username="alice",
            email_confirmed=False,
        )

        with (
            patch(
                "app.auth.services.email_confirm.get_cache_adapter",
                return_value=cache,
            ),
            patch(
                "app.auth.services.email_confirm.UserRepository.get_by_login",
                new=AsyncMock(return_value=user),
            ) as get_by_login,
            patch(
                "app.auth.services.email_confirm.secrets.token_urlsafe",
                return_value="confirm-token",
            ),
        ):
            await EmailConfirmService.send_token(
                "Alice@Example.com",
                background,
                session=Mock(),
            )

        get_by_login.assert_awaited_once_with("alice@example.com", unittest.mock.ANY)
        cache.set.assert_awaited_once_with(
            "email-confirm:alice@example.com",
            "confirm-token",
            EMAIL_CONFIRM_TOKEN_EXPIRE_TIME,
        )
        background.add_task.assert_called_once()
        self.assertEqual(background.add_task.call_args.args[1:], (
            "alice@example.com",
            "alice",
            "confirm-token",
        ))

    async def test_send_token_rejects_already_confirmed_user(self) -> None:
        cache = Mock()
        cache.set = AsyncMock()
        background = Mock()
        user = SimpleNamespace(email_confirmed=True)

        with (
            patch(
                "app.auth.services.email_confirm.get_cache_adapter",
                return_value=cache,
            ),
            patch(
                "app.auth.services.email_confirm.UserRepository.get_by_login",
                new=AsyncMock(return_value=user),
            ),
        ):
            with self.assertRaises(HTTPException) as error:
                await EmailConfirmService.send_token(
                    "alice@example.com",
                    background,
                    session=Mock(),
                )

        self.assertEqual(error.exception.status_code, status.HTTP_400_BAD_REQUEST)
        cache.set.assert_not_awaited()
        background.add_task.assert_not_called()

    async def test_confirm_token_updates_user_and_writes_action_log(self) -> None:
        cache = Mock()
        cache.get = AsyncMock(return_value="confirm-token")
        session = Mock()
        user = SimpleNamespace(uuid=uuid4(), email_confirmed=False)

        with (
            patch(
                "app.auth.services.email_confirm.get_cache_adapter",
                return_value=cache,
            ),
            patch(
                "app.auth.services.email_confirm.UserRepository.get_by_login",
                new=AsyncMock(return_value=user),
            ) as get_by_login,
            patch(
                "app.auth.services.email_confirm.UserRepository.update_email_confirm",
                new=AsyncMock(),
            ) as update_email_confirm,
            patch(
                "app.auth.services.email_confirm.SystemLoggingService.log_user_action",
                new=AsyncMock(),
            ) as log_user_action,
        ):
            await EmailConfirmService.confirm_token(
                "Alice@Example.com",
                "confirm-token",
                session,
            )

        cache.get.assert_awaited_once_with("email-confirm:alice@example.com")
        get_by_login.assert_awaited_once_with("alice@example.com", session)
        update_email_confirm.assert_awaited_once_with(user, session)
        log_user_action.assert_awaited_once_with(
            session,
            action="email_confirmed",
            actor_user_uuid=user.uuid,
            entity_type="user",
            entity_uuid=user.uuid,
        )

    async def test_confirm_token_rejects_invalid_token_before_user_lookup(self) -> None:
        cache = Mock()
        cache.get = AsyncMock(return_value="stored-token")

        with (
            patch(
                "app.auth.services.email_confirm.get_cache_adapter",
                return_value=cache,
            ),
            patch(
                "app.auth.services.email_confirm.UserRepository.get_by_login",
                new=AsyncMock(),
            ) as get_by_login,
        ):
            with self.assertRaises(HTTPException) as error:
                await EmailConfirmService.confirm_token(
                    "alice@example.com",
                    "wrong-token",
                    session=Mock(),
                )

        self.assertEqual(error.exception.status_code, status.HTTP_400_BAD_REQUEST)
        get_by_login.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()

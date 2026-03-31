from loguru import logger

from app.adapters.mail.base_adapter import BaseSMTPAdapter
from app.adapters.mail.mail_message import EmailMessage


class SMTPMockAdapter(BaseSMTPAdapter):

    async def connect(self) -> None:

        logger.info("✅ Подключение к SMTP серверу выполнено")

    async def disconnect(self) -> None:

        logger.info("🔌 Отключение от SMTP сервера выполнено")

    async def send(self, message: EmailMessage) -> None: # pyright: ignore[reportIncompatibleMethodOverride]

        logger.info(message)
        logger.info(f"📤 Письмо отправлено на {message['To']}")

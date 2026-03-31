from email.message import EmailMessage

from aiosmtplib import SMTP, SMTPException
from loguru import logger

from app.adapters.mail.base_adapter import BaseSMTPAdapter


class SMTPAdapter(BaseSMTPAdapter):

    async def connect(self) -> None:

        self._smtp = SMTP(
            hostname=self.host,
            port=self.port,
            use_tls=self.use_tls,
            start_tls=self.use_starttls,
        )
        
        try:
            await self._smtp.connect()
        except SMTPException as e:
            logger.critical(f"Не удалось подключится к SMPT серверу {self.host}:{self.port}.")
            msg = f"Не удалось подключится к SMPT серверу {self.host}:{self.port}."
            raise SMTPException(msg) from e

        if self.username and self.password:
            await self._smtp.login(self.username, self.password)

        logger.info(f"✅ Подключение к SMTP серверу {self.host}:{self.port} выполнено")

    async def disconnect(self) -> None:

        if self._smtp:
            await self._smtp.quit()
            logger.info("🔌 Отключение от SMTP сервера выполнено")
            self._smtp = None

    async def send(self, message: EmailMessage) -> None:

        if not self._smtp:
            msg = "Метод send используется вне async with SMTPClient()"
            raise SMTPException(msg)

        try:
            await self._smtp.send_message(message)
            logger.info(f"📤 Письмо отправлено на {message['To']}")
        except SMTPException as e:
            logger.error(f"❌ Не удалось отправить письмо на {message['To']}: {e}")
            raise

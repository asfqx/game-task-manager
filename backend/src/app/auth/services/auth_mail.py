from pydantic import EmailStr

from app.adapters.mail import EmailMessage, SMTPManager
from app.auth.constant import WELCOME_MESSAGE_PLAIN_TEXT
from app.adapters.mail.base_service import BaseMailService


class AuthMailService(BaseMailService):

    @classmethod
    async def send_welcome_mail(
        cls,
        to: EmailStr,
        username: str,
    ) -> None:

        WELCOME_MESSAGE_SUBJECT = "Добро пожаловать в Task_manager!"

        template = cls.get_template("welcome.html")
        html_content = await template.render_async(username=username)

        message = EmailMessage()

        message["To"] = to
        message["Subject"] = WELCOME_MESSAGE_SUBJECT

        message.set_content(WELCOME_MESSAGE_PLAIN_TEXT)
        message.add_alternative(html_content, subtype="html")

        async with SMTPManager() as smtp_client:
            await smtp_client.send(message)

    @classmethod
    async def send_password_reset_email(
        cls,
        to: EmailStr,
        username: str,
        token: str,
    ) -> None:

        PASSWORD_RESET_MESSAGE_SUBJECT = "Сброс пароля в Task_manager"

        template = cls.get_template("password_reset.html")
        html_content = await template.render_async(username=username, token=token)

        message = EmailMessage()

        message["To"] = to
        message["Subject"] = PASSWORD_RESET_MESSAGE_SUBJECT

        message.set_content(f"Код для сброса пароля: {token}")
        message.add_alternative(html_content, subtype="html")

        async with SMTPManager() as smtp_client:
            await smtp_client.send(message)

    @classmethod
    async def send_email_confirm(
        cls,
        to: EmailStr,
        username: str,
        token: str,
    ) -> None:
        
        EMAIL_CONFIRM_MESSAGE_SUBJECT = "Подтверждение почты в Task_manager"

        template = cls.get_template("email_confirm.html")
        html_content = await template.render_async(username=username, token=token)

        message = EmailMessage()

        message["To"] = to
        message["Subject"] = EMAIL_CONFIRM_MESSAGE_SUBJECT

        message.set_content(f"Код для подтверждения почты: {token}")
        message.add_alternative(html_content, subtype="html")

        async with SMTPManager() as smtp_client:
            await smtp_client.send(message)

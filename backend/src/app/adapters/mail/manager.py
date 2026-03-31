from app.core import settings
from app.adapters.mail.base_adapter import BaseSMTPAdapter

from .adapters import SMTPAdapter, SMTPMockAdapter


class SMTPManager:

    def __new__(
        cls,
        host: str = settings.smtp_mail_host,
        port: int = settings.smtp_mail_port,
        username: str = settings.smtp_mail_username,
        password: str = settings.smtp_mail_password,
        *,
        use_tls: bool = settings.smtp_mail_ssl_tls,
        use_starttls: bool = settings.smtp_mail_starttls,
    ) -> BaseSMTPAdapter:

        if settings.smtp_debug:
            return SMTPMockAdapter(
                host,
                port,
                username,
                password,
                use_tls=use_tls,
                use_starttls=use_starttls,
            )

        return SMTPAdapter(
            host,
            port,
            username,
            password,
            use_tls=use_tls,
            use_starttls=use_starttls,
        )
        

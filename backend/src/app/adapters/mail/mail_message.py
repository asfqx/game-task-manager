from email.message import EmailMessage as BuiltinEmailMessage
from typing import Any

from app.core import settings


class EmailMessage(BuiltinEmailMessage):

    def __init__(
        self,
        *args: tuple[Any],
        **kwargs: dict[Any, Any],
    ) -> None:

        super().__init__(*args, **kwargs) # pyright: ignore[reportArgumentType]

        self['From'] = settings.smtp_mail_from

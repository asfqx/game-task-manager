from abc import ABC, abstractmethod
from email.message import EmailMessage
from types import TracebackType

from aiosmtplib import SMTP


class BaseSMTPAdapter(ABC):

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        *,
        use_tls: bool,
        use_starttls: bool,
    ) -> None:

        self._smtp: SMTP | None = None

        self.host = host
        self.port = port
        self.use_tls = use_tls
        self.use_starttls = use_starttls
        self.username = username
        self.password = password


    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def send(self, message: EmailMessage) -> None: ...

    async def __aenter__(self) -> "BaseSMTPAdapter":

        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:

        await self.disconnect()

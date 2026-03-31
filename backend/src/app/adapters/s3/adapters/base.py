from abc import ABC, abstractmethod
from datetime import timedelta
from io import BytesIO

from minio.helpers import ObjectWriteResult  # pyright: ignore[reportMissingTypeStubs]
from urllib3 import BaseHTTPResponse


class BaseS3StorageAdapter(ABC):

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
    ) -> None:

        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key

    @abstractmethod
    def create_bucket(self, bucket_name: str) -> None:
        ...

    @abstractmethod
    def is_exists(self, bucket_name: str, object_name: str) -> bool:
        ...

    @abstractmethod
    def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta,
    ) -> str:
        ...

    @abstractmethod
    def put(
        self,
        bucket_name: str,
        object_name: str,
        buffer: BytesIO,
        length: int,
        content_type: str
    ) -> ObjectWriteResult:
        ...

    @abstractmethod
    def get(
        self,
        bucket_name: str,
        object_name: str,
    ) -> BaseHTTPResponse | None:
        ...

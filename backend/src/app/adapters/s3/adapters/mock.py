from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
import tempfile
from urllib.parse import quote_plus

from minio.helpers import ObjectWriteResult  # pyright: ignore[reportMissingTypeStubs]
from urllib3 import BaseHTTPResponse

from .base import BaseS3StorageAdapter


class MockAdapter(BaseS3StorageAdapter):

    def __init__(
        self,
        endpoint: str = "http://localhost:9000",
        access_key: str = "mock_access",
        secret_key: str = "mock_secret",
        storage_dir: str | Path | None = None,
    ) -> None:
        super().__init__(endpoint, access_key, secret_key)

        self._storage_dir = Path(
            storage_dir or Path(tempfile.gettempdir()) / "mock_s3_storage"
        )
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def _bucket_path(self, bucket_name: str) -> Path:

        return self._storage_dir / bucket_name

    def _object_path(self, bucket_name: str, object_name: str) -> Path:

        return self._bucket_path(bucket_name) / object_name

    def create_bucket(self, bucket_name: str) -> None:

        self._bucket_path(bucket_name).mkdir(parents=True, exist_ok=True)

    def is_exists(self, bucket_name: str, object_name: str) -> bool:

        return self._object_path(bucket_name, object_name).exists()

    def put_object(self, bucket_name: str, object_name: str, data: bytes) -> None:

        path = self._object_path(bucket_name, object_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get_object(self, bucket_name: str, object_name: str) -> bytes:

        return self._object_path(bucket_name, object_name).read_bytes()

    def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta,
    ) -> str:

        expire_ts = int((datetime.now(UTC) + expires).timestamp())
        return (
            f"{self.endpoint}/mock/{quote_plus(bucket_name)}/{quote_plus(object_name)}"
            f"?expires={expire_ts}&mock=true"
        )

    def put(
        self,
        bucket_name: str,
        object_name: str,
        buffer: BytesIO,
        length: int,
        content_type: str
    ) -> ObjectWriteResult:

        raise NotImplementedError

    def get(
        self,
        bucket_name: str,
        object_name: str,
    ) -> BaseHTTPResponse:

        raise NotImplementedError

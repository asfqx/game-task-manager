from app.core import settings

from .adapters import BaseS3StorageAdapter, MinioAdapter, MockAdapter


class S3StorageManager:

    def __new__(cls) -> BaseS3StorageAdapter:

        match settings.s3_provider:

            case 'minio':
                return MinioAdapter(
                    endpoint=settings.s3_url,
                    access_key=settings.s3_access_key,
                    secret_key=settings.s3_secret_key,
                )

            case 'mock':
                return MockAdapter()


s3_adapter = S3StorageManager()

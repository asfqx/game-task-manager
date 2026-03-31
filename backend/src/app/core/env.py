from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn, RedisDsn, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger


CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[2]
BACKEND_DIR = CURRENT_FILE.parents[3]


class FastAPISettings:
    
    app_host: str = "localhost"
    app_port: int = 8000 
    app_title: str = "task_managment"
    app_description: str = "task_managment"
    api_prefix: str = "/api/v1/auth"
    debug: bool = False
    


class SMTPSettings:
    
    smtp_mail_username: str = ""
    smtp_mail_password: str = ""
    smtp_mail_from: str = ""
    smtp_mail_port: int = 0
    smtp_mail_host: str = ""
    smtp_mail_starttls: bool = False
    smtp_mail_ssl_tls: bool = False
    smtp_debug: bool = True


class DBSettings:
    
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "task_db"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    
    @property
    def db_url(self) -> str:
        
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=f"{self.postgres_db}"
        ).unicode_string()
    
    
class CacheAdapter:

    cache_adapter: str = "redis"
    cache_adapter_host: str = "localhost"
    cache_adapter_port: int = 6379

    @property
    def cache_url(self) -> str:

        if self.cache_adapter.lower() in ("redis", "keydb"):
            return RedisDsn.build(
                scheme=self.cache_adapter.lower(),
                host=self.cache_adapter_host,
                port=self.cache_adapter_port,
            ).unicode_string()

        return ""


class S3Settings:

    s3_provider: Literal['minio', 'mock'] = "minio"
    s3_url: str = "localhost:9000"
    s3_access_key: str = "USERNAME"
    s3_secret_key: str = "PASSWORD"


class JWTSettings:

    hash_secret_key: str = "fghb37483n27453rhe8v758"
    access_token_expire_minutes: int = 324572
    refresh_token_expire_days: int = 341876

    
class Settings(
    BaseSettings,
    FastAPISettings,
    DBSettings,
    JWTSettings,
    CacheAdapter,
    SMTPSettings,
    S3Settings,
):
    
    model_config = SettingsConfigDict(
        env_file=(
            BACKEND_DIR / ".env",
            SRC_DIR / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    

try:
    settings = Settings()
    logger.success("Загрузка настроек прошла успешно")
    
except ValidationError as e:
    logger.error(f"Ошибка в загрузке настроек: {e}")
    

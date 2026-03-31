from uuid import UUID, uuid4
from datetime import datetime, UTC, timedelta

from fastapi import HTTPException, status

from app.auth.type import AuthJWTPayload
from app.core import settings
from app.security import JWTUtils


class JWTTokenService:
    
    @staticmethod
    def create_access_token(
        uuid: UUID,
        role: str,
        *,
        expire_minutes: int = settings.access_token_expire_minutes,
    ) -> str:
        
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=expire_minutes)
        
        payload: AuthJWTPayload = {
            "sub": str(uuid),
            "role": role,
            "exp": expire,
            "iat": now,
            "jti": str(uuid4()),
        }
        
        return JWTUtils.encode(payload=payload)
    
    @staticmethod
    def create_refresh_token(
        uuid: UUID,
        role: str,
        *,
        expire_days: int = settings.refresh_token_expire_days,
    ) -> str:
        
        now = datetime.now(UTC)
        expire = now + timedelta(days=expire_days)
        
        payload: AuthJWTPayload = {
            "sub": str(uuid),
            "role": role,
            "exp": expire,
            "iat": now,
            "jti": str(uuid4()),
        }
        
        return JWTUtils.encode(payload=payload)
        
    @staticmethod
    def get_uuid_from_token(token: str) -> str:
        
        try:
            payload = JWTUtils.decode(token)
        except:
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail="Не удалось декодировать токен",
            )
            
        uuid = payload.get("sub")
        
        if uuid is None:
                        raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail="Передан неверный или истекший токен",
            )
                        
        exp = payload.get("exp")

        if not exp or datetime.now(UTC).timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Переданный токен истек"
            )
            
        return uuid

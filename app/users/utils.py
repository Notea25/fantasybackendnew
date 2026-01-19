import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import parse_qsl, unquote

from jose import JWTError, jwt

from app.config import settings
from app.utils.exceptions import (
    AuthenticationFailedException,
    InvalidDataException,
    InvalidSignatureException,
)

logger = logging.getLogger(__name__)


def validate_telegram_data(init_data: str) -> dict:
    try:
        pairs = parse_qsl(init_data, keep_blank_values=True)
        hash_val = None
        filtered = []

        for k, v in pairs:
            if k == "hash":
                hash_val = v
            else:
                filtered.append((k, v))

        if not hash_val:
            logger.error("Hash is missing in init data")
            raise InvalidSignatureException()

        filtered.sort(key=lambda kv: kv[0])
        data_check_string = "\n".join(f"{k}={v}" for k, v in filtered)

        secret_key = hmac.new(
            b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode("utf-8"), hashlib.sha256
        ).digest()
        calc_hash = hmac.new(
            secret_key, data_check_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calc_hash, hash_val):
            logger.error(
                f"Hash mismatch. Calculated: {calc_hash}, Received: {hash_val}"
            )
            raise InvalidSignatureException()

        auth_date = None
        for k, v in filtered:
            if k == "auth_date":
                try:
                    auth_date = int(v)
                except ValueError:
                    continue

        if not auth_date:
            logger.error("auth_date is missing or invalid")
            raise InvalidSignatureException()

        now = int(time.time())
        if abs(now - auth_date) > 3600:
            logger.error(f"Init data expired. Current: {now}, Auth: {auth_date}")
            raise AuthenticationFailedException()

        result = {k: v for k, v in filtered}
        if "user" in result:
            try:
                result["user"] = json.loads(unquote(result["user"]))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse user JSON: {e}")
                raise InvalidDataException()

        return result
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise AuthenticationFailedException()


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("exp") and payload["exp"] < time.time():
            logger.debug("Token expired")
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except JWTError:
        logger.debug("Invalid token")
        return None
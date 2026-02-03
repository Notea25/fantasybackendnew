import logging

from fastapi import Request

from app.config import settings
from app.users.schemas import UserCreateSchema
from app.users.services import UserService
from app.users.utils import validate_telegram_data, verify_token
from app.utils.exceptions import (
    AuthenticationFailedException,
    InvalidDataException,
)

logger = logging.getLogger(__name__)

async def get_dev_user():
    dev_user = await UserService.get_by_id(1)
    if not dev_user:
        dev_user_data = UserCreateSchema(username="dev_user")
        dev_user = await UserService.add_one(dev_user_data, id=1)
    return dev_user

async def get_by_id(user_id: int):
    return await UserService.find_one_or_none(id=user_id)


async def get_current_user(request: Request):
    if settings.MODE == "DEV" or settings.MODE == "DEVFRONT":
        logger.debug("Running in DEV mode, returning dev user")
        return await get_dev_user()

    try:
        # 1. Пытаемся достать токен из заголовка Authorization
        token: str | None = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

        # 2. Если в заголовке нет — пробуем куку access_token
        if not token:
            cookie_token = request.cookies.get("access_token")
            if cookie_token:
                if cookie_token.startswith("Bearer "):
                    cookie_token = cookie_token[7:]
                token = cookie_token

        if token:
            logger.debug("Found token, attempting to verify")
            try:
                payload = verify_token(token)
                if payload:
                    user_id = payload.get("sub")
                    if user_id:
                        user = await UserService.get_by_telegram_id(int(user_id))
                        if user:
                            logger.debug(f"User authenticated via token: {user.id}")
                            return user
                        logger.warning(f"User not found for valid token (ID: {user_id})")
            except Exception as e:
                logger.warning(f"Token verification failed: {str(e)}")

        # 3. Если токена нет/невалиден
        # Для большинства эндпоинтов просто считаем пользователя неавторизованным.
        # Fallback на Telegram initData разрешаем только для эндпоинта логина.
        path = request.url.path or ""
        if "/users/login" not in path:
            logger.debug("No valid JWT token and not a login endpoint - raising auth error")
            raise AuthenticationFailedException()

        logger.debug("Token invalid or missing on /users/login, falling back to init_data")
        init_data = await request.body()
        init_data_str = init_data.decode("utf-8")
        data = validate_telegram_data(init_data_str)
        user_data = data.get("user", {})
        if not user_data or "id" not in user_data:
            logger.error("Invalid user data in init_data")
            raise InvalidDataException()
        telegram_id = int(user_data["id"])
        user = await UserService.get_by_telegram_id(telegram_id)
        if not user:
            logger.info(f"Creating new user with Telegram ID: {telegram_id}")
            tg_username = user_data.get("username") or ""
            # Generate unique username from telegram_id if username is empty
            username = f"user_{telegram_id}"
            user_create_schema = UserCreateSchema(
                username=username,
                tg_username=tg_username,
                photo_url=user_data.get("photo_url", "").replace("\\/", "/"),
            )
            user = await UserService.add_one(user_data=user_create_schema, id=telegram_id)
            logger.info(f"New user created: ID={user.id}")
        return user
    except InvalidDataException as e:
        logger.error(f"Invalid data: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        raise AuthenticationFailedException()
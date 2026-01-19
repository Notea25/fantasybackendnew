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
        token = request.cookies.get("access_token")
        if token:
            logger.debug("Found token in cookies, attempting to verify")
            try:
                if token.startswith("Bearer "):
                    token = token[7:]
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
        logger.debug("Token invalid or missing, falling back to init_data")
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
            username = user_data.get("username") or f"user_{telegram_id}"
            user_create_schema = UserCreateSchema(
                username=username,
                photo_url=user_data.get("photo_url", "").replace("\\/", "/"),
                emblem_url=None,
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
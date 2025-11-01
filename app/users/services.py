import logging
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import async_session_maker
from app.utils.base_service import BaseService
from app.utils.exceptions import (UsernameGenerationFailedException)
from app.users.models import User

logger = logging.getLogger(__name__)


class UserService(BaseService):
    model = User

    @classmethod
    async def generate_unique_username(cls, session: AsyncSession = None) -> str:
        close_session = False
        if not session:
            session = await cls._get_session()
            close_session = True

        try:
            max_attempts = 100
            for attempt in range(max_attempts):
                random_num = random.randint(100000, 999999)
                username = f"user{random_num}"

                result = await session.execute(
                    select(User).where(User.username == username)
                )
                if not result.scalar_one_or_none():
                    logger.debug(
                        f"Generated unique username: {username} (attempt {attempt + 1})"
                    )
                    return username

            logger.error("Failed to generate unique username after 100 attempts")
            raise UsernameGenerationFailedException()
        finally:
            if close_session:
                await session.close()

    @classmethod
    async def get_by_telegram_id(cls, telegram_id: int):
        logger.debug(f"Searching for user with Telegram ID: {telegram_id}")
        user = await cls.find_one_or_none(id=telegram_id)
        if user:
            logger.debug(f"Found user: {user.id}")
        else:
            logger.debug(f"No user found with Telegram ID: {telegram_id}")
        return user

    @classmethod
    async def add_one(cls, **data):
        logger.debug(f"Creating new user with data: {data}")
        async with async_session_maker() as session:
            try:
                username = await cls.generate_unique_username(session)
                user_data = {**data, "username": username}
                user = cls.model(**user_data)
                session.add(user)
                await session.commit()
                await session.refresh(user)
                logger.debug(f"New user created: {user.id}")
                return user
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating user: {str(e)}", exc_info=True)
                raise

    @classmethod
    async def get_by_id(cls, user_id: int):
        logger.debug(f"Searching for user with ID: {user_id}")
        async with async_session_maker() as session:
            query = select(cls.model).where(cls.model.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            if user:
                logger.debug(f"Found user: {user.id}")
            else:
                logger.debug(f"No user found with ID: {user_id}")
            return user
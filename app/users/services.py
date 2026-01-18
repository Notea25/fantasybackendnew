import logging

from sqlalchemy.future import select

from app.database import async_session_maker
from app.users.models import User
from app.users.schemas import UserCreateSchema, UserUpdateSchema
from app.utils.base_service import BaseService

logger = logging.getLogger(__name__)

class UserService(BaseService):
    model = User

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
    async def add_one(cls, user_data: UserCreateSchema, id: int):
        logger.debug(f"Creating new user with data: {user_data}")
        async with async_session_maker() as session:
            try:
                user = cls.model(id=id, **user_data.model_dump(exclude_unset=True))
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

    @classmethod
    async def update_user(cls, user_id: int, user_data: UserUpdateSchema):
        logger.debug(f"Updating user with ID: {user_id}")
        async with async_session_maker() as session:
            try:
                user = await session.get(cls.model, user_id)
                if not user:
                    logger.debug(f"No user found with ID: {user_id}")
                    return None

                for key, value in user_data.model_dump(exclude_unset=True).items():
                    setattr(user, key, value)

                await session.commit()
                await session.refresh(user)
                logger.debug(f"User updated: {user.id}")
                return user
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating user: {str(e)}", exc_info=True)
                raise
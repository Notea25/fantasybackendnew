import logging
from datetime import datetime

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

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
                user = cls.model(
                    id=id,
                    registration_date=datetime.utcnow(),
                    **user_data.model_dump(exclude_unset=True),
                )
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
                    # Only set referrer_id if it's not already set
                    if key == 'referrer_id' and user.referrer_id is not None:
                        logger.debug(f"Skipping referrer_id update - already set to {user.referrer_id}")
                        continue
                    setattr(user, key, value)

                await session.commit()
                await session.refresh(user)
                logger.debug(f"User updated: {user.id}")
                return user
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating user: {str(e)}", exc_info=True)
                raise
    
    @classmethod
    async def get_referrer(cls, user_id: int):
        """Get the referrer (inviter) of a user."""
        logger.debug(f"Getting referrer for user ID: {user_id}")
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .options(selectinload(cls.model.referrer))
                .where(cls.model.id == user_id)
            )
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.debug(f"User not found with ID: {user_id}")
                return None
            
            return user.referrer
    
    @classmethod
    async def get_referrals(cls, user_id: int, page: int = 1, page_size: int = 10):
        """Get paginated list of users referred by this user."""
        logger.debug(f"Getting referrals for user ID: {user_id}, page: {page}, page_size: {page_size}")
        async with async_session_maker() as session:
            # Count total referrals
            count_query = select(func.count()).select_from(cls.model).where(cls.model.referrer_id == user_id)
            total_result = await session.execute(count_query)
            total = total_result.scalar_one()
            
            # Get paginated referrals
            offset = (page - 1) * page_size
            query = (
                select(cls.model)
                .where(cls.model.referrer_id == user_id)
                .order_by(cls.model.registration_date.desc())
                .limit(page_size)
                .offset(offset)
            )
            result = await session.execute(query)
            referrals = result.scalars().all()
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "referrals": referrals
            }

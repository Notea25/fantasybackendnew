from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.database import async_session_maker
from app.custom_leagues.models import CustomLeague, CustomLeagueType
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, CustomLeagueException, NotAllowedException

class CustomLeagueService(BaseService):
    model = CustomLeague

    @classmethod
    async def create_custom_league(cls, data: dict, user_id: int):
        async with async_session_maker() as session:
            # Проверяем, что пользователь может создать только 1 USER лигу
            if data.get('type') == CustomLeagueType.USER:
                stmt = select(cls.model).where(
                    cls.model.creator_id == user_id,
                    cls.model.type == CustomLeagueType.USER
                )
                result = await session.execute(stmt)
                existing_league = result.scalars().first()
                if existing_league:
                    raise CustomLeagueException()

            # Администратор может создавать коммерческие и клубные лиги
            if data.get('type') in [CustomLeagueType.COMMERCIAL, CustomLeagueType.CLUB]:
                # В реальном приложении здесь должна быть проверка на админа
                pass

            custom_league = cls.model(**data, creator_id=user_id)
            session.add(custom_league)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise NotAllowedException("Failed to create custom league")
            return custom_league

    @classmethod
    async def delete_custom_league(cls, custom_league_id: int, user_id: int):
        async with async_session_maker() as session:
            stmt = select(cls.model).where(cls.model.id == custom_league_id)
            result = await session.execute(stmt)
            custom_league = result.scalars().first()
            if not custom_league:
                raise ResourceNotFoundException()

            # Только создатель или админ может удалить лигу
            if custom_league.creator_id != user_id:
                raise NotAllowedException("Only creator can delete this league")

            await session.delete(custom_league)
            await session.commit()
            return custom_league

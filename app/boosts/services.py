from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from datetime import datetime
from app.database import async_session_maker
from app.boosts.models import Boost, BoostType
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

class BoostService(BaseService):
    model = Boost

    @classmethod
    async def apply_boost(cls, squad_id: int, tour_id: int, boost_type: BoostType):
        async with async_session_maker() as session:
            # Проверяем, что буст не использован в этом туре
            stmt = select(cls.model).where(
                cls.model.squad_id == squad_id,
                cls.model.tour_id == tour_id
            )
            result = await session.execute(stmt)
            if result.scalars().first():
                raise FailedOperationException("Boost already used in this tour")

            boost = cls.model(
                squad_id=squad_id,
                tour_id=tour_id,
                type=boost_type
            )
            session.add(boost)
            await session.commit()
            return boost

    @classmethod
    async def get_available_boosts(cls, squad_id: int, tour_id: int):
        """Возвращает доступные бусты для сквада в текущем туре"""
        async with async_session_maker() as session:
            # Получаем сквад с информацией о бустах
            from app.squads.models import Squad
            stmt = (
                select(Squad)
                .where(Squad.id == squad_id)
                .options(
                    joinedload(Squad.used_boosts).where(Boost.tour_id == tour_id)
                )
            )
            result = await session.execute(stmt)
            squad = result.scalars().first()

            if not squad:
                raise ResourceNotFoundException("Squad not found")

            used_in_tour = any(
                boost.tour_id == tour_id
                for boost in squad.used_boosts
            )

            return {
                "available_boosts": squad.available_boosts > 0 and not used_in_tour,
                "remaining_boosts": squad.available_boosts,
                "used_in_current_tour": used_in_tour,
                "boosts": [
                    {
                        "type": boost_type.value,
                        "description": cls.model.get_description(boost_type),
                        "available": squad.available_boosts > 0 and not used_in_tour
                    }
                    for boost_type in BoostType
                ]
            }

    @classmethod
    async def get_squad_boosts(cls, squad_id: int):
        """Возвращает все бусты сквада"""
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.squad_id == squad_id)
                .options(
                    joinedload(cls.model.tour)
                )
                .order_by(cls.model.used_at.desc())
            )
            result = await session.execute(stmt)
            return result.scalars().all()

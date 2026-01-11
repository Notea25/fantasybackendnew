from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import func, delete

from app.boosts.schemas import BoostType
from app.database import async_session_maker
from app.boosts.models import Boost
from app.squads.models import Squad
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

class BoostService(BaseService):
    model = Boost

    @classmethod
    async def apply_boost(cls, squad_id: int, tour_id: int, boost_type: str):
        async with async_session_maker() as session:
            stmt = select(cls.model).where(
                cls.model.squad_id == squad_id,
                cls.model.tour_id == tour_id
            )
            result = await session.execute(stmt)
            if result.scalars().first():
                raise FailedOperationException("Boost already used in this tour")

            used_boost_type = await session.scalar(
                select(func.count(cls.model.id)).where(
                    cls.model.squad_id == squad_id,
                    cls.model.type == boost_type
                )
            )
            if used_boost_type:
                raise FailedOperationException(f"Boost type {boost_type} already used for this squad")

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
        async with async_session_maker() as session:
            squad = await session.get(Squad, squad_id)
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            used_in_tour = await session.scalar(
                select(func.count(cls.model.id)).where(
                    cls.model.squad_id == squad_id,
                    cls.model.tour_id == tour_id
                )
            )

            used_boosts = await session.execute(
                select(cls.model.type, cls.model.tour_id).where(
                    cls.model.squad_id == squad_id
                )
            )
            used_boosts = used_boosts.all()

            used_boosts_dict = {boost_type: tour_id for boost_type, tour_id in used_boosts}

            all_boost_types = [boost_type.value for boost_type in BoostType]
            boosts = []
            for boost_type in all_boost_types:
                available = not used_in_tour and (boost_type not in used_boosts_dict)
                used_in_tour_number = used_boosts_dict.get(boost_type)

                boosts.append({
                    "type": boost_type,
                    "description": cls._get_boost_description(boost_type),
                    "available": available,
                    "used_in_tour_number": used_in_tour_number
                })

            return {
                "used_in_current_tour": bool(used_in_tour),
                "boosts": boosts
            }

    @classmethod
    def _get_boost_description(cls, boost_type: str) -> str:
        descriptions = {
            "bench_boost": "Увеличивает очки запасных игроков",
            "triple_captain": "Утраивает очки капитана",
            "transfers_plus": "Дополнительные трансферы",
            "gold_tour": "Золотой тур",
            "double_bet": "Двойная ставка"
        }
        return descriptions.get(boost_type, "")

    @classmethod
    async def get_squad_boosts(cls, squad_id: int):
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


    @classmethod
    async def remove_boost(cls, squad_id: int, tour_id: int):

        async with async_session_maker() as session:
            stmt = select(cls.model).where(
                cls.model.squad_id == squad_id,
                cls.model.tour_id == tour_id
            )
            result = await session.execute(stmt)
            boost = result.scalars().first()

            if not boost:
                raise ResourceNotFoundException("Boost not found for this squad and tour")

            await session.execute(
                delete(cls.model).where(
                    cls.model.squad_id == squad_id,
                    cls.model.tour_id == tour_id
                )
            )
            await session.commit()
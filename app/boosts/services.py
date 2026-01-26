from datetime import datetime, timezone

from sqlalchemy import delete, func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.boosts.models import Boost
from app.boosts.schemas import BoostType
from app.database import async_session_maker
from app.squads.models import Squad
from app.utils.base_service import BaseService
from app.utils.exceptions import (
    FailedOperationException,
    ResourceNotFoundException,
)
from app.tours.models import Tour
from app.tours.services import TourService


class BoostService(BaseService):
    model = Boost

    @classmethod
    async def apply_boost(cls, squad_id: int, tour_id: int, boost_type: str):
        async with async_session_maker() as session:
            # Проверяем, что сквад существует
            squad = await session.get(Squad, squad_id)
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            # Определяем previous/current/next туры для лиги сквада
            previous_tour, current_tour, next_tour = await TourService.get_previous_current_next_tour(
                league_id=squad.league_id
            )

            if not next_tour:
                # Нет следующего тура — бусты использовать нельзя
                raise FailedOperationException(
                    "Boosts can only be applied when there is a next tour"
                )

            if tour_id != next_tour.id:
                # Бусты можно использовать только для следующего тура
                raise FailedOperationException(
                    "Boosts can only be applied for the next tour"
                )

            # Разрешаем использовать бусты только до дедлайна тура
            deadline = next_tour.deadline
            if deadline is not None:
                now = datetime.utcnow().replace(tzinfo=timezone.utc)
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                if now > deadline:
                    raise FailedOperationException(
                        "Boosts can only be applied before the tour deadline"
                    )

            # В этом туре уже есть какой-то буст
            stmt = select(cls.model).where(
                cls.model.squad_id == squad_id,
                cls.model.tour_id == tour_id
            )
            result = await session.execute(stmt)
            if result.scalars().first():
                raise FailedOperationException(
                    "Boost already used in this tour"
                )

            # Этот тип уже использовался когда-либо
            used_boost_type = await session.scalar(
                select(func.count(cls.model.id)).where(
                    cls.model.squad_id == squad_id,
                    cls.model.type == boost_type
                )
            )
            if used_boost_type:
                raise FailedOperationException(
                    f"Boost type {boost_type} already used for this squad"
                )

            boost = cls.model(
                squad_id=squad_id,
                tour_id=tour_id,
                type=boost_type,
            )
            session.add(boost)
            await session.commit()
            await session.refresh(boost)
            return boost

    @classmethod
    async def get_available_boosts(cls, squad_id: int, tour_id: int):
        async with async_session_maker() as session:
            squad = await session.get(Squad, squad_id)
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            # Определяем previous/current/next туры для лиги сквада
            previous_tour, current_tour, next_tour = await TourService.get_previous_current_next_tour(
                league_id=squad.league_id
            )

            next_tour_id = next_tour.id if next_tour else None

            # Все использованные бусты для сквада: type, номер тура, id тура
            used_boosts = await session.execute(
                select(cls.model.type, Tour.number, cls.model.tour_id)
                .join(Tour, cls.model.tour_id == Tour.id)
                .where(cls.model.squad_id == squad_id)
            )
            used_rows = used_boosts.all()

            # type -> (tour_number, tour_id)
            used_boosts_dict = {
                boost_type: (tour_number, t_id)
                for boost_type, tour_number, t_id in used_rows
            }

            # Уже есть буст на следующий тур?
            used_for_next_tour = False
            if next_tour_id is not None:
                used_for_next_tour = any(t_id == next_tour_id for _, (_, t_id) in used_boosts_dict.items())

            all_boost_types = [boost_type.value for boost_type in BoostType]
            boosts: list[dict] = []

            for boost_type in all_boost_types:
                used_info = used_boosts_dict.get(boost_type)
                used_in_tour_number = used_info[0] if used_info else None

                # Доступен, только если:
                # - есть следующий тур
                # - этот тип ещё никогда не использовался
                # - на следующий тур ещё не назначен никакой буст
                available = (
                    next_tour_id is not None
                    and used_info is None
                    and not used_for_next_tour
                )

                boosts.append(
                    {
                        "type": boost_type,
                        "available": available,
                        "used_in_tour_number": used_in_tour_number,
                    }
                )

            return {"used_for_next_tour": bool(used_for_next_tour), "boosts": boosts}

    @classmethod
    def _get_boost_description(cls, boost_type: str) -> str:
        # Оставлено для обратной совместимости, сейчас описание не используется в API
        descriptions = {
            "bench_boost": "Увеличивает очки запасных игроков",
            "triple_captain": "Утраивает очки капитана",
            "transfers_plus": "Дополнительные трансферы",
            "gold_tour": "Золотой тур",
            "double_bet": "Двойная ставка",
        }
        return descriptions.get(boost_type, "")

    @classmethod
    async def get_squad_boosts(cls, squad_id: int):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.squad_id == squad_id)
                .options(joinedload(cls.model.tour))
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
                raise ResourceNotFoundException(
                    "Boost not found for this squad and tour"
                )

            # Проверяем дедлайн тура: бусты можно отменять только до дедлайна
            tour = await session.get(Tour, tour_id)
            if tour and tour.deadline is not None:
                deadline = tour.deadline
                now = datetime.utcnow().replace(tzinfo=timezone.utc)
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                if now > deadline:
                    raise FailedOperationException(
                        "Boosts can only be removed before the tour deadline"
                    )

            # Трансферные бусты нельзя отменять
            if boost.type in (BoostType.TRANSFERS_PLUS.value, BoostType.GOLD_TOUR.value):
                raise FailedOperationException("This boost cannot be removed")

            await session.execute(
                delete(cls.model).where(
                    cls.model.squad_id == squad_id,
                    cls.model.tour_id == tour_id
                )
            )
            await session.commit()

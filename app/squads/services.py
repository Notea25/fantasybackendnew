from typing import Optional, List
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.future import select
from sqlalchemy import delete, and_, or_
from datetime import datetime

from app.players.models import Player
from app.squads.models import (
    Squad, squad_players_association, squad_bench_players_association,
    SquadTour, Boost, BoostType
)
from app.tours.models import Tour
from app.database import async_session_maker
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

class SquadService(BaseService):
    model = Squad

    @classmethod
    async def create_squad(cls, name: str, user_id: int, league_id: int, fav_team_id: int):
        async with async_session_maker() as session:
            # Проверка на существование сквада в этой лиге
            existing_squad = await session.execute(
                select(cls.model).where(
                    cls.model.user_id == user_id,
                    cls.model.league_id == league_id
                )
            )
            if existing_squad.scalars().first():
                raise FailedOperationException("User already has a squad in this league")

            # Найти следующий тур
            next_tour = await cls._get_next_tour(league_id)
            if not next_tour:
                raise FailedOperationException("No available tours for this league")

            squad = cls.model(
                name=name,
                user_id=user_id,
                league_id=league_id,
                fav_team_id=fav_team_id,
                current_tour_id=next_tour.id
            )
            session.add(squad)

            # Создать историю для первого тура
            squad_tour = SquadTour(
                squad_id=squad.id,
                tour_id=next_tour.id,
                is_current=True
            )
            session.add(squad_tour)

            await session.commit()
            await session.refresh(squad)
            return squad

    @classmethod
    async def _get_next_tour(cls, league_id: int) -> Optional[Tour]:
        """Возвращает текущий или следующий тур"""
        async with async_session_maker() as session:
            now = datetime.now()
            # Ищем текущий тур
            stmt = select(Tour).where(
                Tour.league_id == league_id,
                Tour.start_date <= now,
                Tour.end_date >= now
            )
            result = await session.execute(stmt)
            current_tour = result.scalars().first()

            # Если нет текущего, берем первый тур
            if not current_tour:
                stmt = select(Tour).where(
                    Tour.league_id == league_id
                ).order_by(Tour.start_date)
                result = await session.execute(stmt)
                current_tour = result.scalars().first()

            return current_tour

    @classmethod
    async def update_squad_players(cls, squad_id: int, main_player_ids: list[int], bench_player_ids: list[int]):
        async with async_session_maker() as session:
            squad = await session.execute(
                select(cls.model).where(cls.model.id == squad_id)
                .options(
                    selectinload(cls.model.current_main_players),
                    selectinload(cls.model.current_bench_players),
                )
            )
            squad = squad.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")

            players = await session.execute(
                select(Player).where(Player.id.in_(main_player_ids + bench_player_ids))
            )
            players = players.scalars().all()
            player_by_id = {player.id: player for player in players}

            # Проверки
            if len(players) != len(main_player_ids) + len(bench_player_ids):
                raise ResourceNotFoundException("One or more players not found")

            club_counts = {}
            for player_id in main_player_ids + bench_player_ids:
                player = player_by_id[player_id]
                club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1
                if club_counts[player.team_id] > 3:
                    raise FailedOperationException("Cannot add more than 3 players from the same club")

            if len(main_player_ids) > 11:
                raise FailedOperationException("Cannot add more than 11 players to the main squad")
            if len(bench_player_ids) > 4:
                raise FailedOperationException("Cannot add more than 4 players to the bench")

            # Очистка текущих составов
            await session.execute(
                delete(squad_players_association).where(
                    squad_players_association.c.squad_id == squad_id
                )
            )
            await session.execute(
                delete(squad_bench_players_association).where(
                    squad_bench_players_association.c.squad_id == squad_id
                )
            )

            # Обновление составов
            for player_id in main_player_ids:
                stmt = squad_players_association.insert().values(
                    squad_id=squad_id, player_id=player_id
                )
                await session.execute(stmt)

            for player_id in bench_player_ids:
                stmt = squad_bench_players_association.insert().values(
                    squad_id=squad_id, player_id=player_id
                )
                await session.execute(stmt)

            # Сохранение состава для текущего тура
            await cls._save_current_squad(squad_id)

            await session.commit()
            return squad

    @classmethod
    async def apply_boost(cls, squad_id: int, boost_type: BoostType):
        async with async_session_maker() as session:
            squad = await cls._get_squad_with_tour(squad_id)

            # Проверка доступности бустов
            if squad.available_boosts <= 0:
                raise FailedOperationException("No boosts available")

            # Проверка, что буст не использован в этом туре
            if await cls._is_boost_used_in_tour(squad_id, squad.current_tour_id):
                raise FailedOperationException("Boost already used in this tour")

            # Создание записи о бусте
            boost = Boost(
                squad_id=squad_id,
                tour_id=squad.current_tour_id,
                type=boost_type
            )
            session.add(boost)

            # Обновление SquadTour
            stmt = select(SquadTour).where(
                SquadTour.squad_id == squad_id,
                SquadTour.tour_id == squad.current_tour_id
            )
            result = await session.execute(stmt)
            squad_tour = result.scalars().first()

            if squad_tour:
                squad_tour.used_boost = boost_type

            squad.available_boosts -= 1
            await session.commit()
            return squad

    @classmethod
    async def get_available_boosts(cls, squad_id: int):
        """Возвращает информацию о доступных бустах"""
        squad = await cls._get_squad_with_tour(squad_id)

        used_in_tour = await cls._is_boost_used_in_tour(squad_id, squad.current_tour_id)

        boosts_info = [
            {
                "type": boost.value,
                "description": cls._get_boost_description(boost),
                "available": squad.available_boosts > 0 and not used_in_tour
            }
            for boost in BoostType
        ]

        return {
            "available_boosts": squad.available_boosts,
            "used_in_current_tour": used_in_tour,
            "boosts": boosts_info
        }

    @classmethod
    async def find_all_with_relations(cls):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.league),
                    selectinload(cls.model.current_main_players),
                    selectinload(cls.model.current_bench_players),
                )
            )
            result = await session.execute(stmt)
            squads = result.unique().scalars().all()
            return squads

    @classmethod
    async def find_filtered_with_relations(cls, **filter_by):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .filter_by(**filter_by)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.league),
                    selectinload(cls.model.current_main_players).joinedload(Player.stats),
                    selectinload(cls.model.current_bench_players).joinedload(Player.stats),
                )
            )
            result = await session.execute(stmt)
            squads = result.unique().scalars().all()
            return squads

    @classmethod
    async def find_one_or_none_with_relations(cls, **filter_by):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .filter_by(**filter_by)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.league),
                    selectinload(cls.model.current_main_players).selectinload(Player.stats),
                    selectinload(cls.model.current_bench_players).selectinload(Player.stats),
                    joinedload(cls.model.tour_history).joinedload(SquadTour.tour),
                    joinedload(cls.model.tour_history).joinedload(SquadTour.main_players),
                    joinedload(cls.model.tour_history).joinedload(SquadTour.bench_players),
                )
            )
            result = await session.execute(stmt)
            squad = result.unique().scalars().first()
            return squad

    @classmethod
    async def _get_squad_with_tour(cls, squad_id: int):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .where(cls.model.id == squad_id)
                .options(
                    joinedload(cls.model.current_tour),
                    joinedload(cls.model.used_boosts),
                    joinedload(cls.model.tour_history).joinedload(SquadTour.tour),
                    joinedload(cls.model.tour_history).joinedload(SquadTour.main_players),
                    joinedload(cls.model.tour_history).joinedload(SquadTour.bench_players),
                )
            )
            result = await session.execute(stmt)
            squad = result.scalars().first()
            if not squad:
                raise ResourceNotFoundException("Squad not found")
            return squad

    @classmethod
    async def _is_boost_used_in_tour(cls, squad_id: int, tour_id: int) -> bool:
        """Проверяет, использован ли буст в текущем туре"""
        async with async_session_maker() as session:
            stmt = select(Boost).where(
                Boost.squad_id == squad_id,
                Boost.tour_id == tour_id
            )
            result = await session.execute(stmt)
            return result.scalars().first() is not None

    @classmethod
    async def _save_current_squad(cls, squad_id: int):
        """Сохраняет текущий состав для текущего тура"""
        async with async_session_maker() as session:
            squad = await session.execute(
                select(cls.model)
                .where(cls.model.id == squad_id)
                .options(
                    selectinload(cls.model.current_main_players),
                    selectinload(cls.model.current_bench_players)
                )
            )
            squad = squad.scalars().first()

            if not squad or not squad.current_tour_id:
                return

            stmt = select(SquadTour).where(
                SquadTour.squad_id == squad_id,
                SquadTour.tour_id == squad.current_tour_id
            )
            result = await session.execute(stmt)
            squad_tour = result.scalars().first()

            if squad_tour:
                # Обновляем состав и очки
                squad_tour.main_players = squad.current_main_players
                squad_tour.bench_players = squad.current_bench_players
                squad_tour.points = squad.calculate_points()
                await session.commit()

    @classmethod
    def _get_boost_description(cls, boost_type: BoostType) -> str:
        """Возвращает описание буста"""
        descriptions = {
            BoostType.BENCH_BOOST: "Удваивает очки запасных игроков",
            BoostType.TRIPLE_CAPTAIN: "Троит очки капитана",
            BoostType.TRANSFERS_PLUS: "Дополнительные трансферы",
            BoostType.GOLD_TOUR: "Бонусные очки за тур",
            BoostType.DOUBLE_BET: "Удваивает ставку"
        }
        return descriptions.get(boost_type, "")

    @classmethod
    async def get_squad_history(cls, squad_id: int) -> list[SquadTour]:
        """Возвращает историю составов сквада"""
        async with async_session_maker() as session:
            stmt = (
                select(SquadTour)
                .where(SquadTour.squad_id == squad_id)
                .options(
                    joinedload(SquadTour.tour),
                    joinedload(SquadTour.main_players),
                    joinedload(SquadTour.bench_players)
                )
                .order_by(SquadTour.tour_id)
            )
            result = await session.execute(stmt)
            return result.unique().scalars().all()

    @classmethod
    async def get_squad_by_tour(cls, squad_id: int, tour_id: int):
        """Возвращает состав сквада для определенного тура"""
        async with async_session_maker() as session:
            stmt = (
                select(SquadTour)
                .where(
                    SquadTour.squad_id == squad_id,
                    SquadTour.tour_id == tour_id
                )
                .options(
                    joinedload(SquadTour.main_players),
                    joinedload(SquadTour.bench_players),
                    joinedload(SquadTour.tour)
                )
            )
            result = await session.execute(stmt)
            return result.unique().scalars().first()

    @classmethod
    async def update_squad_after_tour(cls, squad_id: int, tour_id: int):
        """Обновляет сквад после завершения тура"""
        async with async_session_maker() as session:
            # Найти следующий тур
            squad = await session.execute(
                select(cls.model).where(cls.model.id == squad_id)
            )
            squad = squad.scalars().first()

            if not squad:
                raise ResourceNotFoundException("Squad not found")

            next_tour = await cls._get_next_tour(squad.league_id)

            # Если есть следующий тур
            if next_tour and next_tour.id != squad.current_tour_id:
                squad.current_tour_id = next_tour.id

                # Создать новую запись в истории
                squad_tour = SquadTour(
                    squad_id=squad.id,
                    tour_id=next_tour.id,
                    is_current=True
                )
                session.add(squad_tour)

                await session.commit()
                return squad
            return None

    @classmethod
    async def get_leaderboard(cls, tour_id: int) -> list[dict]:
        """Возвращает таблицу лидеров для тура"""
        async with async_session_maker() as session:
            stmt = (
                select(SquadTour)
                .where(SquadTour.tour_id == tour_id)
                .options(
                    joinedload(SquadTour.squad).joinedload(Squad.user),
                    joinedload(SquadTour.squad).joinedload(Squad.league)
                )
                .order_by(SquadTour.points.desc())
            )
            result = await session.execute(stmt)
            tours = result.unique().scalars().all()

            return [
                {
                    "position": i + 1,
                    "squad_id": tour.squad_id,
                    "user_id": tour.squad.user_id,
                    "username": tour.squad.user.username,
                    "points": tour.points
                }
                for i, tour in enumerate(tours)
            ]

@classmethod
async def get_squad_boosts(cls, squad_id: int):
    """Возвращает информацию о бустах сквада"""
    async with async_session_maker() as session:
        stmt = (
            select(cls.model)
            .where(cls.model.id == squad_id)
            .options(joinedload(cls.model.used_boosts))
        )
        result = await session.execute(stmt)
        squad = result.scalars().first()

        if not squad:
            raise ResourceNotFoundException("Squad not found")

        return {
            "available_boosts": squad.available_boosts,
            "used_boosts": [
                {
                    "type": boost.type.value,
                    "tour_id": boost.tour_id,
                    "used_at": boost.used_at
                }
                for boost in squad.used_boosts
            ]
        }

@classmethod
async def apply_boost_to_squad(cls, squad_id: int, boost_type: BoostType, tour_id: int):
    """Применяет буст к скваду для определенного тура"""
    async with async_session_maker() as session:
        squad = await cls._get_squad_with_tour(squad_id)

        if squad.available_boosts <= 0:
            raise FailedOperationException("No boosts available")

        # Проверяем, что буст не использован в этом туре
        existing_boost = await session.execute(
            select(Boost).where(
                Boost.squad_id == squad_id,
                Boost.tour_id == tour_id
            )
        )

        if existing_boost.scalars().first():
            raise FailedOperationException("Boost already used in this tour")

        # Создаем новый буст
        boost = Boost(
            squad_id=squad_id,
            tour_id=tour_id,
            type=boost_type,
            used_at=datetime.now()
        )
        session.add(boost)

        # Обновляем SquadTour
        stmt = select(SquadTour).where(
            SquadTour.squad_id == squad_id,
            SquadTour.tour_id == tour_id
        )
        result = await session.execute(stmt)
        squad_tour = result.scalars().first()

        if squad_tour:
            squad_tour.used_boost = boost_type

        squad.available_boosts -= 1
        await session.commit()
        return squad



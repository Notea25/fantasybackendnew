from typing import Optional
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.future import select
from sqlalchemy import delete, func
from datetime import datetime

from app.matches.models import Match
from app.players.models import Player
from app.squads.models import Squad, squad_players_association, squad_bench_players_association, SquadTour
from app.tours.models import Tour, tour_matches_association
from app.database import async_session_maker
from app.utils.base_service import BaseService
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

class SquadService(BaseService):
    model = Squad

    @classmethod
    async def create_squad(
            cls,
            name: str,
            user_id: int,
            league_id: int,
            fav_team_id: int,
            main_player_ids: list[int],
            bench_player_ids: list[int]
    ):
        async with async_session_maker() as session:
            try:
                # Проверка на существование сквада у пользователя в лиге
                existing_squad = await session.execute(
                    select(cls.model).where(
                        cls.model.user_id == user_id,
                        cls.model.league_id == league_id
                    )
                )
                if existing_squad.scalars().first():
                    raise FailedOperationException("User already has a squad in this league")

                # Получаем следующий тур
                next_tour = await cls._get_next_tour(league_id)

                # Получаем всех игроков для проверки
                all_player_ids = main_player_ids + bench_player_ids
                players = await session.execute(
                    select(Player).where(Player.id.in_(all_player_ids))
                )
                players = players.scalars().all()
                player_by_id = {player.id: player for player in players}

                # Проверки
                if len(players) != len(all_player_ids):
                    raise ResourceNotFoundException("One or more players not found")

                # Проверка на количество игроков
                if len(main_player_ids) != 11:
                    raise FailedOperationException("Main squad must have exactly 11 players")
                if len(bench_player_ids) != 4:
                    raise FailedOperationException("Bench must have exactly 4 players")

                # Проверка на бюджет
                total_cost = sum(p.market_value for p in players)
                if total_cost > 100_000:
                    raise FailedOperationException("Total players cost exceeds squad budget")

                # Проверка на лигу
                for player in players:
                    if player.league_id != league_id:
                        raise FailedOperationException("All players must be from the same league")

                # Проверка на количество игроков из одного клуба
                club_counts = {}
                for player in players:
                    club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1
                    if club_counts[player.team_id] > 3:
                        raise FailedOperationException("Cannot have more than 3 players from the same club")

                # Устанавливаем бюджет: 100_000 - стоимость игроков
                budget = 100_000 - total_cost
                if budget < 0:
                    raise FailedOperationException("Budget cannot be negative")

                # Создаем сквад
                squad = cls.model(
                    name=name,
                    user_id=user_id,
                    league_id=league_id,
                    fav_team_id=fav_team_id,
                    current_tour_id=next_tour.id if next_tour else None,
                    budget=budget,
                    replacements=3,
                )
                session.add(squad)

                # Сохраняем сквад, чтобы получить его id
                await session.commit()
                await session.refresh(squad)

                # Добавляем игроков в основной состав
                for player_id in main_player_ids:
                    stmt = squad_players_association.insert().values(
                        squad_id=squad.id, player_id=player_id
                    )
                    await session.execute(stmt)

                # Добавляем игроков в запасной состав
                for player_id in bench_player_ids:
                    stmt = squad_bench_players_association.insert().values(
                        squad_id=squad.id, player_id=player_id
                    )
                    await session.execute(stmt)

                # Создаем запись в истории, если есть следующий тур
                if next_tour:
                    squad_tour = SquadTour(
                        squad_id=squad.id,
                        tour_id=next_tour.id,
                        is_current=True,
                        main_players=players[:11],
                        bench_players=players[11:],
                    )
                    session.add(squad_tour)

                await session.commit()

                return squad

            except Exception as e:
                await session.rollback()
                print(f"Error creating squad: {str(e)}")
                raise FailedOperationException(f"Failed to create squad: {str(e)}")

    @classmethod
    async def _get_next_tour(cls, league_id: int) -> Tour | None:
        now = datetime.utcnow()

        tour_start_dates = (
            select(
                tour_matches_association.c.tour_id,
                func.min(Match.date).label("start_date")
            )
            .join(Match, Match.id == tour_matches_association.c.match_id)
            .group_by(tour_matches_association.c.tour_id)
            .subquery()
        )

        stmt = (
            select(Tour)
            .join(tour_start_dates, Tour.id == tour_start_dates.c.tour_id)
            .where(
                Tour.league_id == league_id,
                tour_start_dates.c.start_date > now
            )
            .order_by(tour_start_dates.c.start_date.asc())
            .limit(1)
        )

        async with async_session_maker() as session:
            result = await session.execute(stmt)
            return result.unique().scalars().first()

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

            await cls._save_current_squad(squad_id)

            await session.commit()
            return squad

    @classmethod
    async def find_all_with_relations(cls):
        async with async_session_maker() as session:
            stmt = (
                select(cls.model)
                .options(
                    joinedload(cls.model.user),
                    joinedload(cls.model.league),
                    selectinload(cls.model.current_main_players).joinedload(Player.match_stats),
                    selectinload(cls.model.current_bench_players).joinedload(Player.match_stats),
                )
            )
            result = await session.execute(stmt)
            squads = result.unique().salars().all()
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
                    selectinload(cls.model.current_main_players).joinedload(Player.match_stats),
                    selectinload(cls.model.current_bench_players).joinedload(Player.match_stats),
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
                    selectinload(cls.model.current_main_players),
                    selectinload(cls.model.current_bench_players),
                )
            )
            result = await session.execute(stmt)
            squad = result.unique().scalars().first()
            return squad

    @classmethod
    async def _save_current_squad(cls, squad_id: int):
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
    async def replace_players(cls, squad_id: int, new_main_players: list[int], new_bench_players: list[int]):
        """
        Заменяет игроков в скваде с учетом ограничений на количество замен и бюджет
        """
        async with async_session_maker() as session:
            # Получаем текущий сквад с игроками
            stmt = (
                select(cls.model)
                .where(cls.model.id == squad_id)
                .options(
                    selectinload(cls.model.current_main_players),
                    selectinload(cls.model.current_bench_players),
                    selectinload(cls.model.league)
                )
            )
            result = await session.execute(stmt)
            squad = result.scalars().first()

            if not squad:
                raise ResourceNotFoundException("Squad not found")

            # Получаем текущих игроков
            current_main_ids = {p.id for p in squad.current_main_players}
            current_bench_ids = {p.id for p in squad.current_bench_players}

            # Преобразуем новые списки в множества для сравнения
            new_main_set = set(new_main_players)
            new_bench_set = set(new_bench_players)

            # Находим отличающихся игроков
            main_diff = len(current_main_ids - new_main_set)
            bench_diff = len(current_bench_ids - new_bench_set)

            # Проверяем количество замен
            if (main_diff + bench_diff) > squad.replacements:
                raise FailedOperationException(
                    f"Not enough replacements. Available: {squad.replacements}, "
                    f"Required: {main_diff + bench_diff}"
                )

            # Получаем всех игроков для проверки бюджета и лиги
            all_player_ids = new_main_players + new_bench_players
            stmt = select(Player).where(Player.id.in_(all_player_ids))
            result = await session.execute(stmt)
            new_players = result.scalars().all()
            player_by_id = {p.id: p for p in new_players}

            # Проверяем, что все игроки из одной лиги
            league_ids = {p.league_id for p in new_players}
            if len(league_ids) > 1 or league_ids.pop() != squad.league_id:
                raise FailedOperationException("All players must be from the same league")

            # Проверяем бюджет
            total_cost = sum(p.market_value for p in new_players)
            if total_cost > squad.budget:
                raise FailedOperationException("Total players cost exceeds squad budget")

            # Проверяем количество игроков от одного клуба (не более 3)
            club_counts = {}
            for player_id in all_player_ids:
                player = player_by_id[player_id]
                club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1
                if club_counts[player.team_id] > 3:
                    raise FailedOperationException("Cannot have more than 3 players from the same club")

            # Проверяем количество игроков в командах
            if len(new_main_players) > 11:
                raise FailedOperationException("Main squad cannot have more than 11 players")
            if len(new_bench_players) > 4:
                raise FailedOperationException("Bench cannot have more than 4 players")

            # Очищаем текущие составы
            await session.execute(
                delete(squad_players_association)
                .where(squad_players_association.c.squad_id == squad_id)
            )
            await session.execute(
                delete(squad_bench_players_association)
                .where(squad_bench_players_association.c.squad_id == squad_id)
            )

            # Добавляем новых игроков
            for player_id in new_main_players:
                stmt = squad_players_association.insert().values(
                    squad_id=squad_id, player_id=player_id
                )
                await session.execute(stmt)

            for player_id in new_bench_players:
                stmt = squad_bench_players_association.insert().values(
                    squad_id=squad_id, player_id=player_id
                )
                await session.execute(stmt)

            # Обновляем количество доступных замен
            squad.replacements -= (main_diff + bench_diff)

            # Обновляем очки сквада
            squad.points = squad.calculate_points()

            await session.commit()
            await session.refresh(squad)
            return squad

    @classmethod
    async def get_replacement_info(cls, squad_id: int) -> dict:
        """
        Возвращает информацию о доступных заменах и бюджете
        """
        async with async_session_maker() as session:
            stmt = select(cls.model).where(cls.model.id == squad_id)
            result = await session.execute(stmt)
            squad = result.scalars().first()

            if not squad:
                raise ResourceNotFoundException("Squad not found")

            return {
                "available_replacements": squad.replacements,
                "budget": squad.budget,
                "current_players_cost": sum(p.market_value for p in squad.current_main_players) +
                                      sum(p.market_value for p in squad.current_bench_players)
            }

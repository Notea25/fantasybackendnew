from sqlalchemy.orm import joinedload

from app.matches.models import Match
from app.player_match_stats.models import PlayerMatchStats
from app.teams.models import Team
from app.utils.base_service import BaseService
import logging
from sqlalchemy.future import select
from app.database import async_session_maker

logger = logging.getLogger(__name__)

class PlayerMatchStatsService(BaseService):
    model = PlayerMatchStats

    @classmethod
    async def find_all(cls, player_id: int = None, match_id: int = None):
        async with async_session_maker() as session:
            if player_id:
                stmt = select(cls.model).where(cls.model.player_id == player_id)
            elif match_id:
                stmt = select(cls.model).where(cls.model.match_id == match_id)
            else:
                stmt = select(cls.model)
            result = await session.execute(stmt)
            stats = result.unique().scalars().all()
            return stats

    @classmethod
    async def add_empty_stats_for_match(cls, match_id: int):
        async with async_session_maker() as session:
            # Получить матч с подгруженными командами и игроками
            stmt = (
                select(Match)
                .where(Match.id == match_id)
                .options(
                    joinedload(Match.home_team).joinedload(Team.players),
                    joinedload(Match.away_team).joinedload(Team.players)
                )
            )
            result = await session.execute(stmt)
            match = result.unique().scalars().first()  # Добавили вызов unique()

            if not match:
                logger.error(f"Match with id {match_id} not found")
                return 0

            # Получить всех игроков обеих команд
            home_players = match.home_team.players if match.home_team else []
            away_players = match.away_team.players if match.away_team else []

            # Создать пустые записи для каждого игрока
            stats_to_add = []
            for player in home_players + away_players:
                stats = cls.model(
                    player_id=player.id,
                    match_id=match.id,
                    team_id=player.team_id,
                    league_id=match.league_id,
                )
                stats_to_add.append(stats)

            # Добавить все записи в базу
            session.add_all(stats_to_add)
            await session.commit()
            logger.info(f"Added empty stats for {len(stats_to_add)} players in match {match_id}")

            return len(stats_to_add)

    @classmethod
    async def add_empty_stats_for_all_matches(cls):
        async with async_session_maker() as session:
            # Получить все матчи с подгруженными командами и игроками
            stmt = (
                select(Match)
                .options(
                    joinedload(Match.home_team).joinedload(Team.players),
                    joinedload(Match.away_team).joinedload(Team.players)
                )
            )
            result = await session.execute(stmt)
            matches = result.unique().scalars().all()

            total_added = 0
            for match in matches:
                # Получить всех игроков обеих команд
                home_players = match.home_team.players if match.home_team else []
                away_players = match.away_team.players if match.away_team else []

                # Создать пустые записи для каждого игрока
                stats_to_add = []
                for player in home_players + away_players:
                    # Проверить, есть ли уже статистика для этого игрока в этом матче
                    existing_stmt = select(cls.model).where(
                        cls.model.player_id == player.id,
                        cls.model.match_id == match.id
                    )
                    existing = await session.execute(existing_stmt)
                    if not existing.scalar_one_or_none():
                        stats = cls.model(
                            player_id=player.id,
                            match_id=match.id,
                            team_id=player.team_id,
                            league_id=match.league_id,
                        )
                        stats_to_add.append(stats)

                if stats_to_add:
                    session.add_all(stats_to_add)
                    await session.commit()
                    logger.info(f"Added empty stats for {len(stats_to_add)} players in match {match.id}")
                    total_added += len(stats_to_add)

            logger.info(f"Added empty stats for total {total_added} players in all matches")
            return total_added
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select

from app.base_service import BaseService
from app.database import async_session_maker
from app.player_match_stats.models import PlayerMatchStats
from app.player_match_stats.schemas import PlayerTotalStats
from app.exceptions import ResourceNotFoundException

class PlayerMatchStatsService(BaseService):
    model = PlayerMatchStats

    @classmethod
    async def get_player_total_stats(cls, player_id: int) -> PlayerTotalStats:
        async with async_session_maker() as session:
            # Используем select с joinedload для загрузки связанных данных
            stmt = (
                select(cls.model)
                .where(cls.model.player_id == player_id)
                .options(
                    joinedload(cls.model.player),
                    joinedload(cls.model.league),
                    joinedload(cls.model.team),
                )
            )
            result = await session.execute(stmt)
            stats_list = result.scalars().all()

            if not stats_list:
                raise ResourceNotFoundException()

            # Получаем данные первого объекта для заполнения информации об игроке, команде и лиге
            first_stat = stats_list[0]

            # Агрегируем данные
            total_stats = PlayerTotalStats(
                player_name=first_stat.player.name,
                position=first_stat.position,
                league_name=first_stat.league.name,
                team_name=first_stat.team.name,
                total_minutes_played=sum(stat.minutes_played for stat in stats_list),
                total_matches=len(stats_list),
                total_yellow_cards=sum(stat.yellow_cards for stat in stats_list),
                total_yellow_red_cards=sum(stat.yellow_red_cards for stat in stats_list),
                total_red_cards=sum(stat.red_cards for stat in stats_list),
                total_goals=sum(stat.goals_total for stat in stats_list),
                total_assists=sum(stat.assists for stat in stats_list),
                total_goals_conceded=sum(stat.goals_conceded for stat in stats_list),
                total_saves=sum(stat.saves for stat in stats_list),
                total_penalty_saved=sum(stat.penalty_saved for stat in stats_list),
                total_penalty_missed=sum(stat.penalty_missed for stat in stats_list),
                total_points=sum(stat.points for stat in stats_list),
                clean_sheets=sum(1 for stat in stats_list if stat.position == "G" and stat.goals_conceded == 0),
            )

            return total_stats

from app.base_service import BaseService
from app.player_match_stats.models import PlayerMatchStats
from app.player_match_stats.schemas import PlayerTotalStats
from app.exceptions import ResourceNotFoundException

class PlayerMatchStatsService(BaseService):
    model = PlayerMatchStats

    @classmethod
    async def get_player_total_stats(cls, player_id: int) -> PlayerTotalStats:
        stats_list = await cls.find_filtered(player_id=player_id)
        if not stats_list:
            raise ResourceNotFoundException()

        total_stats = PlayerTotalStats(
            player_name=stats_list[0].player.name,
            position=stats_list[0].position,
            league_name=stats_list[0].league.name,
            team_name=stats_list[0].team.name,
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

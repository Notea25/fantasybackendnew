from celery import current_app as celery_app
from app.player_stats.services import PlayerStatsService
import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

@celery_app.task(name="update_player_stats")
def update_player_stats(league_id: int = 116):
    try:
        sync_to_async(PlayerStatsService.add_player_stats_for_league)(league_id)
        logger.info(f"Successfully updated player stats for league {league_id}")
    except Exception as e:
        logger.error(f"Failed to update player stats for league {league_id}: {e}")
        raise

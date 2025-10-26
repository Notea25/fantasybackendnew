from fastapi import APIRouter
from app.player_match_stats.schemas import PlayerMatchStats, PlayerTotalStats
from app.player_match_stats.services import PlayerMatchStatsService
from app.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/player_match_stats", tags=["Player Match Stats"])

@router.get("/player_id_{player_id}/match_id_{match_id}")
async def get_player_match_stats(player_id: int, match_id: int) -> PlayerMatchStats:
    stats = await PlayerMatchStatsService.find_one_or_none(player_id=player_id, match_id=match_id)
    if not stats:
        raise ResourceNotFoundException
    return stats

@router.get("/player_id_{player_id}/total_stats")
async def get_player_total_stats(player_id: int) -> PlayerTotalStats:
    return await PlayerMatchStatsService.get_player_total_stats(player_id)


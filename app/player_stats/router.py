from fastapi import APIRouter

from app.player_stats.schemas import PlayerStats
from app.player_stats.services import PlayerStatsService
from app.utils.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/player_stats", tags=["Player Stats"])

@router.get("/player_id_{player_id}")
async def get_player_stats(player_id: int) -> PlayerStats:
    stats = await PlayerStatsService.find_one_or_none(player_id=player_id)
    if not stats:
        raise ResourceNotFoundException
    return stats



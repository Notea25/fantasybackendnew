from fastapi import APIRouter
from app.player_match_stats.schemas import PlayerMatchStats
from app.player_match_stats.services import PlayerMatchStatsService
from app.utils.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/player_match_stats", tags=["Player Match Stats"])

@router.get("/player_id_{player_id}")
async def get_player_match_stats(player_id: int) -> list[PlayerMatchStats]:
    stats = await PlayerMatchStatsService.find_all(player_id=player_id)
    if not stats:
        raise ResourceNotFoundException
    return stats
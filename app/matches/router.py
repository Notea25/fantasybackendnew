from fastapi import APIRouter, Depends, HTTPException

from app.matches.schemas import MatchSchema
from app.matches.services import MatchService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/all")
async def list_matches() -> list[MatchSchema]:
    return await MatchService.find_all()

@router.get("/id_{match_id}")
async def get_match(match_id: int) -> MatchSchema:
    res = await MatchService.find_one_or_none(id=match_id)
    if not res:
        raise ResourceNotFoundException
    return res

@router.get("/league_{league_id}")
async def get_matches_by_league(league_id: int) -> list[MatchSchema]:
    res = await MatchService.find_filtered(league_id=league_id)
    if not res:
        raise ResourceNotFoundException
    return res

@router.get("/team/{team_id}")
async def get_matches_by_team(team_id: int) -> list[MatchSchema]:
    res = await MatchService.find_matches_by_team(team_id=team_id)
    if not res:
        raise ResourceNotFoundException
    return res

@router.post("/finalize/{match_id}")
async def finalize_match(
    match_id: int,
    user: User = Depends(get_current_user)
) -> dict:
    """Финализировать матч и начислить очки всем SquadTour.
    
    Этот эндпоинт вызывается администратором после завершения матча.
    При финализации:
    1. Матч помечается как завершённый (is_finished=True)
    2. Для каждого игрока в PlayerMatchStats находятся все SquadTour,
       где этот игрок в основном составе
    3. Очки игрока за матч прибавляются к очкам SquadTour
    
    TODO: Добавить проверку прав доступа (только для админов)
    
    Args:
        match_id: ID завершённого матча
    
    Returns:
        Информация о количестве обновлённых SquadTour и начисленных очков
    """
    # TODO: Добавить проверку: if not user.is_admin: raise HTTPException(403)
    
    try:
        result = await MatchService.finalize_match(match_id=match_id)
        return {
            "status": "success",
            "message": f"Match {match_id} finalized successfully",
            **result
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to finalize match: {str(e)}"
        )

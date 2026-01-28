from fastapi import APIRouter, Depends, HTTPException

from app.custom_leagues.commercial_league.schemas import CommercialLeagueSchema
from app.custom_leagues.commercial_league.services import CommercialLeagueService
from app.custom_leagues.user_league.services import UserLeagueService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException, NotAllowedException

router = APIRouter(prefix="/commercial_leagues", tags=["Commercial Leagues"])

@router.get("/", response_model=list[CommercialLeagueSchema])
async def get_commercial_leagues(league_id: int = None):
    try:
        commercial_leagues = await CommercialLeagueService.get_commercial_leagues(league_id)
        return commercial_leagues
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{commercial_league_id}", response_model=CommercialLeagueSchema)
async def get_commercial_league_by_id(commercial_league_id: int):
    try:
        commercial_league = await CommercialLeagueService.get_commercial_league_by_id(commercial_league_id)
        # Manually add winner_name to the response
        winner_name = commercial_league.winner.name if commercial_league.winner else None
        
        # Convert to dict and add winner_name
        league_dict = {
            "id": commercial_league.id,
            "name": commercial_league.name,
            "league_id": commercial_league.league_id,
            "prize": commercial_league.prize,
            "logo": commercial_league.logo,
            "winner_id": commercial_league.winner_id,
            "winner_name": winner_name,
            "registration_start": commercial_league.registration_start,
            "registration_end": commercial_league.registration_end,
            "tours": [{"id": tour.id, "number": tour.number} for tour in commercial_league.tours],
            "squads": [{"squad_id": squad.id, "squad_name": squad.name} for squad in commercial_league.squads]
        }
        return league_dict
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{commercial_league_id}/leaderboard/{tour_id}", response_model=list[dict])
async def get_commercial_league_leaderboard(commercial_league_id: int, tour_id: int):
    leaderboard = await CommercialLeagueService.get_commercial_league_leaderboard(commercial_league_id, tour_id)
    if not leaderboard:
        raise HTTPException(status_code=404, detail="No data found for this commercial league and tour")
    return leaderboard


@router.post("/join/{commercial_league_id}/{squad_id}")
async def join_commercial_league(
    commercial_league_id: int,
    squad_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        result = await CommercialLeagueService.join_commercial_league(squad_id, commercial_league_id)
        return {"message": "Squad successfully joined the commercial league", "result": result}
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAllowedException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
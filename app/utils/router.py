from fastapi import APIRouter
from app.leagues.services import LeagueService
from app.matches.services import MatchService
from app.players.services import PlayerService
from app.teams.services import TeamService
from app.exceptions import AlreadyExistsException, ExternalAPIErrorException, FailedOperationException

router = APIRouter(prefix="/utils", tags=["Utils"])

@router.post("/add_league_{league_id}")
async def add_league(league_id: int):
    try:
        league = await LeagueService.add_league(league_id)
        return {"status": "success", "league_id": league.id, "league_name": league.name}
    except AlreadyExistsException:
        raise
    except ExternalAPIErrorException:
        raise
    except Exception as e:
        raise FailedOperationException(msg=f"Failed to add league: {e}")

@router.post("/add_teams_{league_id}")
async def add_teams(league_id: int):
    try:
        await TeamService.add_teams(league_id)
        return {"status": "success", "league_id": league_id}
    except AlreadyExistsException:
        raise
    except ExternalAPIErrorException:
        raise
    except Exception as e:
        raise FailedOperationException(msg=f"Failed to add teams: {e}")

@router.post("/add_players_{league_id}")
async def add_players(league_id: int):
    try:
        await PlayerService.add_players_for_league(league_id)
        return {"status": "success", "league_id": league_id}
    except AlreadyExistsException:
        raise
    except ExternalAPIErrorException:
        raise
    except Exception as e:
        raise FailedOperationException(msg=f"Failed to add players: {e}")


@router.post("/add_matches_{league_id}")
async def add_matches(league_id: int):
    try:
        await MatchService.add_matches_for_league(league_id)
        return {"status": "success", "league_id": league_id}
    except ExternalAPIErrorException:
        raise
    except Exception as e:
        raise FailedOperationException(msg=f"Failed to add matches: {e}")
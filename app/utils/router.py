import logging
from fastapi import APIRouter
from app.leagues.services import LeagueService
from app.matches.services import MatchService
from app.player_stats.services import PlayerStatsService
from app.players.services import PlayerService
from app.teams.services import TeamService
from app.utils.exceptions import AlreadyExistsException, ExternalAPIErrorException, FailedOperationException


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utils", tags=["Utils"])

@router.post("/add_league_{league_id}")
async def add_league(league_id: int):
    try:
        await LeagueService.add_league(league_id)
        return {"status": "success", "league_id": league_id}
    except ExternalAPIErrorException as e:
        raise e
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


@router.post("/add_player_stats_{league_id}")
async def add_player_stats(league_id: int):
    try:
        await PlayerStatsService.add_player_stats_for_league(league_id)
        return {"status": "success", "league_id": league_id}
    except FailedOperationException:
        raise
    except ExternalAPIErrorException:
        raise
    except Exception as e:
        raise FailedOperationException(msg=f"Failed to add player stats: {e}")


@router.post("/add_all")
async def add_all():
    league_id = 116
    try:
        await LeagueService.add_league(league_id)
        await TeamService.add_teams(league_id)
        await PlayerService.add_players_for_league(league_id)
        await MatchService.add_matches_for_league(league_id)
        await PlayerStatsService.add_player_stats_for_league(league_id)
        return {"status": "success", "league_id": league_id}
    except AlreadyExistsException as e:
        logger.warning(f"Some entities already exist for league {league_id}: {e}")
        raise
    except ExternalAPIErrorException as e:
        logger.error(f"External API error for league {league_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to add all entities for league {league_id}: {e}")
        raise FailedOperationException(msg=f"Failed to add all entities: {e}")
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from app.squads.services import SquadService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

router = APIRouter(prefix="/squads", tags=["Squads"])

@router.get("/list_squads", response_model=List[Dict[str, Any]])
async def list_squads() -> List[Dict[str, Any]]:
    squads = await SquadService.find_all_with_relations()
    squads_data = []
    for squad in squads:
        squad_data = {
            "id": squad.id,
            "name": squad.name,
            "user_id": squad.user.id,
            "username": squad.user.username,
            "league_id": squad.league_id,
            "fav_team_id": squad.fav_team_id,
            "budget": squad.budget,
            "replacements": squad.replacements,
            "main_players": getattr(squad, 'main_players_data', []),
            "bench_players": getattr(squad, 'bench_players_data', [])
        }
        squads_data.append(squad_data)
    return squads_data

@router.post("/create", response_model=Dict[str, Any])
async def create_squad(
    name: str,
    league_id: int,
    fav_team_id: int,
    main_player_ids: List[int],
    bench_player_ids: List[int],
    user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    squad = await SquadService.create_squad(
        name=name,
        user_id=user.id,
        league_id=league_id,
        fav_team_id=fav_team_id,
        main_player_ids=main_player_ids,
        bench_player_ids=bench_player_ids,
    )
    squad_with_relations = await SquadService.find_one_or_none_with_relations(id=squad.id)
    squad_data = {
        "id": squad_with_relations.id,
        "name": squad_with_relations.name,
        "user_id": squad_with_relations.user.id,
        "username": squad_with_relations.user.username,
        "league_id": squad_with_relations.league_id,
        "fav_team_id": squad_with_relations.fav_team_id,
        "budget": squad_with_relations.budget,
        "replacements": squad_with_relations.replacements,
        "main_players": getattr(squad_with_relations, 'main_players_data', []),
        "bench_players": getattr(squad_with_relations, 'bench_players_data', [])
    }
    return squad_data

@router.get("/my_squads", response_model=List[Dict[str, Any]])
async def list_users_squads(user: User = Depends(get_current_user)) -> List[Dict[str, Any]]:
    squads = await SquadService.find_filtered_with_relations(user_id=user.id)
    squads_data = []
    for squad in squads:
        squad_data = {
            "id": squad.id,
            "name": squad.name,
            "user_id": squad.user.id,
            "username": squad.user.username,
            "league_id": squad.league_id,
            "fav_team_id": squad.fav_team_id,
            "budget": squad.budget,
            "replacements": squad.replacements,
            "main_players": getattr(squad, 'main_players_data', []),
            "bench_players": getattr(squad, 'bench_players_data', [])
        }
        squads_data.append(squad_data)
    return squads_data

@router.get("/get_squad_{squad_id}", response_model=Dict[str, Any])
async def get_squad(squad_id: int, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    squad = await SquadService.find_one_or_none_with_relations(id=squad_id, user_id=user.id)
    if not squad:
        raise ResourceNotFoundException()
    squad_data = {
        "id": squad.id,
        "name": squad.name,
        "user_id": squad.user.id,
        "username": squad.user.username,
        "league_id": squad.league_id,
        "fav_team_id": squad.fav_team_id,
        "budget": squad.budget,
        "replacements": squad.replacements,
        "main_players": getattr(squad, 'main_players_data', []),
        "bench_players": getattr(squad, 'bench_players_data', [])
    }
    return squad_data

@router.put("/update_players/{squad_id}", response_model=Dict[str, Any])
async def update_squad_players(
    squad_id: int,
    main_player_ids: List[int],
    bench_player_ids: List[int],
    user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    squad = await SquadService.update_squad_players(
        squad_id=squad_id,
        main_player_ids=main_player_ids,
        bench_player_ids=bench_player_ids
    )
    squad_with_relations = await SquadService.find_one_or_none_with_relations(id=squad.id)
    squad_data = {
        "id": squad_with_relations.id,
        "name": squad_with_relations.name,
        "user_id": squad_with_relations.user.id,
        "username": squad_with_relations.user.username,
        "league_id": squad_with_relations.league_id,
        "fav_team_id": squad_with_relations.fav_team_id,
        "budget": squad_with_relations.budget,
        "replacements": squad_with_relations.replacements,
        "main_players": getattr(squad_with_relations, 'main_players_data', []),
        "bench_players": getattr(squad_with_relations, 'bench_players_data', [])
    }
    return {"status": "success", "message": "Squad players updated", "squad": squad_data}

@router.get("/{squad_id}/history", response_model=List[Dict[str, Any]])
async def get_squad_history(squad_id: int, user: User = Depends(get_current_user)) -> List[Dict[str, Any]]:
    squad = await SquadService.find_one_or_none_with_relations(id=squad_id)
    if not squad:
        raise ResourceNotFoundException()
    return squad.tour_history

@router.get("/leaderboard/{tour_id}", response_model=List[Dict[str, Any]])
async def get_leaderboard(tour_id: int) -> List[Dict[str, Any]]:
    return await SquadService.get_leaderboard(tour_id)

@router.post("/{squad_id}/replace_players", response_model=Dict[str, Any])
async def replace_players(
    squad_id: int,
    main_player_ids: List[int],
    bench_player_ids: List[int],
    user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    squad = await SquadService.replace_players(
        squad_id=squad_id,
        new_main_players=main_player_ids,
        new_bench_players=bench_player_ids
    )
    squad_with_relations = await SquadService.find_one_or_none_with_relations(id=squad.id)
    squad_data = {
        "id": squad_with_relations.id,
        "name": squad_with_relations.name,
        "user_id": squad_with_relations.user.id,
        "username": squad_with_relations.user.username,
        "league_id": squad_with_relations.league_id,
        "fav_team_id": squad_with_relations.fav_team_id,
        "budget": squad_with_relations.budget,
        "replacements": squad_with_relations.replacements,
        "main_players": getattr(squad_with_relations, 'main_players_data', []),
        "bench_players": getattr(squad_with_relations, 'bench_players_data', [])
    }
    return {
        "status": "success",
        "message": "Players replaced successfully",
        "remaining_replacements": squad.replacements,
        "squad": squad_data
    }

@router.get("/{squad_id}/replacement_info", response_model=Dict[str, Any])
async def get_replacement_info(
    squad_id: int,
    user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    return await SquadService.get_replacement_info(squad_id)

@router.patch("/{squad_id}/rename", response_model=Dict[str, Any])
async def rename_squad(squad_id: int, new_name: str, user: User = Depends(get_current_user)) -> Dict[str, Any]:
    squad = await SquadService.rename_squad(squad_id=squad_id, user_id=user.id, new_name=new_name)
    return {
        "id": squad.id,
        "name": squad.name,
        "user_id": squad.user_id,
        "league_id": squad.league_id,
        "fav_team_id": squad.fav_team_id,
        "budget": squad.budget,
        "replacements": squad.replacements
    }

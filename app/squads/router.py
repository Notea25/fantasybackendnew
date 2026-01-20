from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.squads.schemas import (
    LeaderboardEntrySchema,
    ReplacementInfoSchema,
    SquadReadSchema,
    SquadRenameSchema,
    SquadReplacePlayersResponseSchema,
    SquadTourHistorySchema,
    SquadUpdateResponseSchema,
    SquadCreateSchema,
    SquadUpdatePlayersSchema,
)
from app.squads.services import SquadService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

router = APIRouter(prefix="/squads", tags=["Squads"])

@router.get("/list_squads", response_model=list[SquadReadSchema])
async def list_squads() -> list[SquadReadSchema]:
    squads = await SquadService.find_all_with_relations()
    return squads

@router.post("/create", response_model=SquadReadSchema)
async def create_squad(
    squad_data: SquadCreateSchema,
    user: User = Depends(get_current_user),
) -> SquadReadSchema:
    squad = await SquadService.create_squad(
        name=squad_data.name,
        user_id=user.id,
        league_id=squad_data.league_id,
        fav_team_id=squad_data.fav_team_id,
        captain_id=squad_data.captain_id,
        vice_captain_id=squad_data.vice_captain_id,
        main_player_ids=squad_data.main_player_ids,
        bench_player_ids=squad_data.bench_player_ids,
    )
    squad_with_relations = await SquadService.find_one_or_none_with_relations(id=squad.id)
    return squad_with_relations

@router.get("/my_squads", response_model=list[SquadReadSchema])
async def list_users_squads(user: User = Depends(get_current_user)) -> list[SquadReadSchema]:
    squads = await SquadService.find_filtered_with_relations(user_id=user.id)
    return squads

@router.get("/get_squad_{squad_id}", response_model=SquadReadSchema)
async def get_squad(squad_id: int, user: User = Depends(get_current_user)) -> SquadReadSchema:
    squad = await SquadService.find_one_or_none_with_relations(id=squad_id, user_id=user.id)
    if not squad:
        raise ResourceNotFoundException()
    return squad

@router.put("/update_players/{squad_id}", response_model=SquadUpdateResponseSchema)
async def update_squad_players(
    squad_id: int,
    payload: SquadUpdatePlayersSchema,
    user: User = Depends(get_current_user),
) -> SquadUpdateResponseSchema:
    main_player_ids = payload.main_player_ids or []
    bench_player_ids = payload.bench_player_ids or []

    squad = await SquadService.update_squad_players(
        squad_id=squad_id,
        captain_id=payload.captain_id,
        vice_captain_id=payload.vice_captain_id,
        main_player_ids=main_player_ids,
        bench_player_ids=bench_player_ids,
    )
    squad_with_relations = await SquadService.find_one_or_none_with_relations(id=squad.id)
    return SquadUpdateResponseSchema(
        status="success",
        message="Squad players updated",
        squad=squad_with_relations
    )

@router.post("/{squad_id}/replace_players", response_model=SquadReplacePlayersResponseSchema)
async def replace_players(
    squad_id: int,
    captain_id: Optional[int] = None,
    vice_captain_id: Optional[int] = None,
    payload: SquadUpdatePlayersSchema = None,
    user: User = Depends(get_current_user),
) -> SquadReplacePlayersResponseSchema:
    payload = payload or SquadUpdatePlayersSchema()
    main_player_ids = payload.main_player_ids or []
    bench_player_ids = payload.bench_player_ids or []

    squad = await SquadService.replace_players(
        squad_id=squad_id,
        captain_id=captain_id,
        vice_captain_id=vice_captain_id,
        new_main_players=main_player_ids,
        new_bench_players=bench_player_ids,
    )
    squad_with_relations = await SquadService.find_one_or_none_with_relations(id=squad.id)
    return SquadReplacePlayersResponseSchema(
        status="success",
        message="Players replaced successfully",
        remaining_replacements=squad.replacements,
        squad=squad_with_relations
    )

@router.get("/{squad_id}/replacement_info", response_model=ReplacementInfoSchema)
async def get_replacement_info(
    squad_id: int,
    user: User = Depends(get_current_user)
) -> ReplacementInfoSchema:
    return await SquadService.get_replacement_info(squad_id)

@router.patch("/{squad_id}/rename", response_model=SquadRenameSchema)
async def rename_squad(squad_id: int, new_name: str, user: User = Depends(get_current_user)) -> SquadRenameSchema:
    squad = await SquadService.rename_squad(squad_id=squad_id, user_id=user.id, new_name=new_name)
    return squad

@router.get("/{squad_id}/history", response_model=list[SquadTourHistorySchema])
async def get_squad_history(squad_id: int, user: User = Depends(get_current_user)) -> list[SquadTourHistorySchema]:
    squad = await SquadService.find_one_or_none_with_relations(id=squad_id)
    if not squad:
        raise ResourceNotFoundException()
    return squad.tour_history

@router.get("/leaderboard/{tour_id}", response_model=list[LeaderboardEntrySchema])
async def get_leaderboard(tour_id: int) -> list[LeaderboardEntrySchema]:
    return await SquadService.get_leaderboard(tour_id)

@router.get("/leaderboard/{tour_id}/by-fav-team/{fav_team_id}", response_model=list[LeaderboardEntrySchema])
async def get_leaderboard_by_fav_team(tour_id: int, fav_team_id: int) -> list[LeaderboardEntrySchema]:
    return await SquadService.get_leaderboard_by_fav_team(tour_id, fav_team_id)
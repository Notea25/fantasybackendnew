from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)

from app.squads.schemas import (
    SquadReadSchema,
    SquadRenameSchema,
    SquadUpdateResponseSchema,
    SquadCreateSchema,
    SquadUpdatePlayersSchema,
)
from app.squad_tours.schemas import (
    LeaderboardEntrySchema,
    PublicLeaderboardEntrySchema,
    PublicClubLeaderboardEntrySchema,
    ReplacementInfoSchema,
    SquadTourReplacePlayersResponseSchema,
    SquadTourHistorySchema,
)
from app.squads.services import SquadService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException, FailedOperationException

router = APIRouter(prefix="/squads", tags=["Squads"])

@router.get("/list_squads", response_model=list[SquadReadSchema])
async def list_squads() -> list[SquadReadSchema]:
    """List all squads (metadata only)."""
    squads = await SquadService.find_all_with_user()
    # Add username for response
    for squad in squads:
        squad.username = squad.user.username if squad.user else ""
    return squads

@router.post("/create", response_model=SquadReadSchema)
async def create_squad(
    squad_data: SquadCreateSchema,
    user: User = Depends(get_current_user),
) -> SquadReadSchema:
    """Create squad (returns metadata only)."""
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
    squad_with_user = await SquadService.find_one_with_user(id=squad.id)
    squad_with_user.username = squad_with_user.user.username if squad_with_user.user else ""
    return squad_with_user

@router.get("/my_squads", response_model=list[SquadReadSchema])
async def list_users_squads(user: User = Depends(get_current_user)) -> list[SquadReadSchema]:
    """List user's squads (metadata only)."""
    squads = await SquadService.find_all_with_user(user_id=user.id)
    for squad in squads:
        squad.username = squad.user.username if squad.user else ""
    return squads

@router.get("/get_squad_{squad_id}", response_model=SquadReadSchema)
async def get_squad(squad_id: int) -> SquadReadSchema:
    """Публичный эндпоинт для получения сквада по ID.
    
    Новая архитектура: возвращает только метаданные Squad.
    Для получения состава используйте /squads/{squad_id}/history.
    """
    squad = await SquadService.find_one_with_user(id=squad_id)
    if not squad:
        raise ResourceNotFoundException()
    squad.username = squad.user.username if squad.user else ""
    return squad


@router.get("/get_squad_by_id/{squad_id}", response_model=SquadReadSchema)
async def get_squad_by_id(squad_id: int) -> SquadReadSchema:
    """Публичный эндпоинт для получения сквада по ID без проверки пользователя.

    Новая архитектура: возвращает только метаданные Squad.
    """
    squad = await SquadService.find_one_with_user(id=squad_id)
    if not squad:
        raise ResourceNotFoundException()
    squad.username = squad.user.username if squad.user else ""
    return squad


@router.put("/update_players/{squad_id}", response_model=SquadUpdateResponseSchema, deprecated=True)
async def update_squad_players(
    squad_id: int,
    payload: SquadUpdatePlayersSchema,
    user: User = Depends(get_current_user),
) -> SquadUpdateResponseSchema:
    """DEPRECATED: Use /squads/{squad_id}/replace_players instead.
    
    This endpoint is deprecated in new architecture.
    Squad now contains only metadata, use SquadTour for player composition.
    """
    raise HTTPException(
        status_code=410,  # Gone
        detail="This endpoint is deprecated. Use POST /squads/{squad_id}/replace_players instead."
    )

@router.post("/{squad_id}/replace_players", response_model=SquadTourReplacePlayersResponseSchema, deprecated=True)
async def replace_players(
    squad_id: int,
    captain_id: Optional[int] = None,
    vice_captain_id: Optional[int] = None,
    payload: SquadUpdatePlayersSchema = None,
    user: User = Depends(get_current_user),
) -> SquadTourReplacePlayersResponseSchema:
    """DEPRECATED: Use POST /squad_tours/squad/{squad_id}/replace_players instead.
    
    This endpoint is deprecated in new architecture.
    Squad now contains only metadata, use SquadTour for player composition.
    """
    raise HTTPException(
        status_code=410,  # Gone
        detail="This endpoint is deprecated. Use POST /squad_tours/squad/{squad_id}/replace_players instead."
    )

@router.get("/{squad_id}/replacement_info", response_model=ReplacementInfoSchema, deprecated=True)
async def get_replacement_info(
    squad_id: int,
    user: User = Depends(get_current_user)
) -> ReplacementInfoSchema:
    """DEPRECATED: Use GET /squad_tours/squad/{squad_id}/replacement_info instead."""
    raise HTTPException(
        status_code=410,  # Gone
        detail="This endpoint is deprecated. Use GET /squad_tours/squad/{squad_id}/replacement_info instead."
    )

@router.patch("/{squad_id}/rename", response_model=SquadRenameSchema)
async def rename_squad(squad_id: int, new_name: str, user: User = Depends(get_current_user)) -> SquadRenameSchema:
    squad = await SquadService.rename_squad(squad_id=squad_id, user_id=user.id, new_name=new_name)
    return squad


@router.get("/{squad_id}/tours", response_model=list[SquadTourHistorySchema], deprecated=True)
async def get_squad_tours(squad_id: int) -> list[SquadTourHistorySchema]:
    """DEPRECATED: Use GET /squad_tours/squad/{squad_id} instead.
    
    Каждый SquadTour - это snapshot состояния сквада для конкретного тура.
    """
    raise HTTPException(
        status_code=410,  # Gone
        detail="This endpoint is deprecated. Use GET /squad_tours/squad/{squad_id} instead."
    )

@router.get("/leaderboard/{tour_id}", response_model=list[PublicLeaderboardEntrySchema])
async def get_leaderboard(tour_id: int) -> list[PublicLeaderboardEntrySchema]:
    return await SquadService.get_leaderboard(tour_id)

@router.get("/leaderboard/{tour_id}/by-fav-team/{fav_team_id}", response_model=list[PublicClubLeaderboardEntrySchema])
async def get_leaderboard_by_fav_team(tour_id: int, fav_team_id: int) -> list[PublicClubLeaderboardEntrySchema]:
    return await SquadService.get_leaderboard_by_fav_team(tour_id, fav_team_id)

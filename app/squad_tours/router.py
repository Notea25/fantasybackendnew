from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging

from app.squad_tours.schemas import (
    SquadTourHistorySchema,
    SquadTourUpdatePlayersSchema,
    SquadTourReplacePlayersResponseSchema,
    ReplacementInfoSchema,
)
from app.matches.models import Match
from app.teams.models import Team
from app.tours.models import Tour, TourMatchAssociation
from app.squad_tours.services import SquadTourService
from app.squads.services import SquadService
from app.users.dependencies import get_current_user
from app.users.models import User
from app.utils.exceptions import ResourceNotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/squad_tours", tags=["Squad Tours"])


async def _get_opponent_map_for_tour(session, tour_id: int) -> dict[int, tuple[str, bool]]:
    """Вернуть для тура отображение team_id -> (opponent_name, is_home).

    Используется сквад-API, чтобы отдать в ответе реального соперника
    для каждого игрока в составе (на основе расписания матчей тура).
    """
    stmt = (
        select(Tour)
        .where(Tour.id == tour_id)
        .options(
            joinedload(Tour.matches_association)
            .joinedload(TourMatchAssociation.match)
            .joinedload(Match.home_team),
            joinedload(Tour.matches_association)
            .joinedload(TourMatchAssociation.match)
            .joinedload(Match.away_team),
        )
    )
    result = await session.execute(stmt)
    tour = result.unique().scalars().first()
    opponent_map: dict[int, tuple[str, bool]] = {}

    if not tour:
        return opponent_map

    for association in tour.matches_association:
        match = association.match
        if not match:
            continue
        home_team: Team | None = match.home_team
        away_team: Team | None = match.away_team
        if home_team and away_team:
            opponent_map[home_team.id] = (away_team.name, True)
            opponent_map[away_team.id] = (home_team.name, False)

    return opponent_map


@router.get("/squad/{squad_id}/tour/{tour_id}", response_model=SquadTourHistorySchema)
async def get_squad_tour(
    squad_id: int,
    tour_id: int
) -> SquadTourHistorySchema:
    """Get SquadTour for specific squad and tour."""
    squad_tour = await SquadTourService.find_by_squad_and_tour(
        squad_id=squad_id,
        tour_id=tour_id,
        with_players=True
    )
    
    if not squad_tour:
        raise HTTPException(
            status_code=404,
            detail=f"SquadTour not found for squad {squad_id} and tour {tour_id}"
        )
    
    # Get tour number
    from app.tours.services import TourService
    tour = await TourService.find_one_or_none(id=tour_id)
    tour_number = tour.number if tour else 0
    
    # Get player points
    from app.database import async_session_maker
    async with async_session_maker() as session:
        opponent_map = await _get_opponent_map_for_tour(session, tour_id)

        main_players_data = []
        for player in squad_tour.main_players:
            total_points = await SquadService._get_player_total_points(session, player.id)
            tour_points = await SquadService._get_player_tour_points(session, player.id, tour_id)
            opponent_info = opponent_map.get(player.team_id)
            
            main_players_data.append({
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "team_id": player.team_id,
                "team_name": player.team.name if player.team else "",
                "team_logo": player.team.logo if player.team else None,
                "market_value": player.market_value,
                "photo": player.photo,
                "total_points": total_points,
                "tour_points": tour_points,
                "next_opponent_team_name": opponent_info[0] if opponent_info else None,
                "next_opponent_is_home": opponent_info[1] if opponent_info else None,
            })
        
        bench_players_data = []
        for player in squad_tour.bench_players:
            total_points = await SquadService._get_player_total_points(session, player.id)
            tour_points = await SquadService._get_player_tour_points(session, player.id, tour_id)
            opponent_info = opponent_map.get(player.team_id)
            
            bench_players_data.append({
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "team_id": player.team_id,
                "team_name": player.team.name if player.team else "",
                "team_logo": player.team.logo if player.team else None,
                "market_value": player.market_value,
                "photo": player.photo,
                "total_points": total_points,
                "tour_points": tour_points,
                "next_opponent_team_name": opponent_info[0] if opponent_info else None,
                "next_opponent_is_home": opponent_info[1] if opponent_info else None,
            })
    
    return SquadTourHistorySchema(
        tour_id=squad_tour.tour_id,
        tour_number=tour_number,
        points=squad_tour.points,
        penalty_points=squad_tour.penalty_points,
        used_boost=squad_tour.used_boost,
        captain_id=squad_tour.captain_id,
        vice_captain_id=squad_tour.vice_captain_id,
        budget=squad_tour.budget,
        replacements=squad_tour.replacements,
        is_finalized=squad_tour.is_finalized,
        main_players=main_players_data,
        bench_players=bench_players_data,
    )


@router.get("/squad/{squad_id}", response_model=List[SquadTourHistorySchema])
async def get_squad_all_tours(
    squad_id: int
) -> List[SquadTourHistorySchema]:
    """Get all SquadTours for a squad (full history)."""
    return await SquadService.get_squad_tour_history_with_players(squad_id)


@router.get("/tour/{tour_id}", response_model=List[SquadTourHistorySchema])
async def get_all_squads_for_tour(
    tour_id: int
) -> List[SquadTourHistorySchema]:
    """Get all SquadTours for a specific tour."""
    squad_tours = await SquadTourService.find_all_by_tour(tour_id=tour_id)
    
    if not squad_tours:
        return []
    
    # Get tour number
    from app.tours.services import TourService
    tour = await TourService.find_one_or_none(id=tour_id)
    tour_number = tour.number if tour else 0
    
    result = []
    from app.database import async_session_maker
    async with async_session_maker() as session:
        opponent_map = await _get_opponent_map_for_tour(session, tour_id)
        for squad_tour in squad_tours:
            # Load relationships if not loaded
            from sqlalchemy.orm import selectinload
            from sqlalchemy import select
            from app.squad_tours.models import SquadTour
            from app.players.models import Player
            
            stmt = (
                select(SquadTour)
                .where(SquadTour.id == squad_tour.id)
                .options(
                    selectinload(SquadTour.main_players).joinedload(Player.team),
                    selectinload(SquadTour.bench_players).joinedload(Player.team)
                )
            )
            loaded_result = await session.execute(stmt)
            loaded_squad_tour = loaded_result.unique().scalars().first()
            
            if not loaded_squad_tour:
                continue
            
            main_players_data = []
            for player in loaded_squad_tour.main_players:
                total_points = await SquadService._get_player_total_points(session, player.id)
                tour_points = await SquadService._get_player_tour_points(session, player.id, tour_id)
                opponent_info = opponent_map.get(player.team_id)
                
                main_players_data.append({
                    "id": player.id,
                    "name": player.name,
                    "position": player.position,
                    "team_id": player.team_id,
                    "team_name": player.team.name if player.team else "",
                    "team_logo": player.team.logo if player.team else None,
                    "market_value": player.market_value,
                    "photo": player.photo,
                    "total_points": total_points,
                    "tour_points": tour_points,
                    "next_opponent_team_name": opponent_info[0] if opponent_info else None,
                    "next_opponent_is_home": opponent_info[1] if opponent_info else None,
                })
            
                bench_players_data = []
                for player in loaded_squad_tour.bench_players:
                    total_points = await SquadService._get_player_total_points(session, player.id)
                    tour_points = await SquadService._get_player_tour_points(session, player.id, tour_id)
                    opponent_info = opponent_map.get(player.team_id)
                    
                    bench_players_data.append({
                    "id": player.id,
                    "name": player.name,
                    "position": player.position,
                    "team_id": player.team_id,
                    "team_name": player.team.name if player.team else "",
                    "team_logo": player.team.logo if player.team else None,
                    "market_value": player.market_value,
                    "photo": player.photo,
                    "total_points": total_points,
                    "tour_points": tour_points,
                    "next_opponent_team_name": opponent_info[0] if opponent_info else None,
                    "next_opponent_is_home": opponent_info[1] if opponent_info else None,
                })
            
            result.append(SquadTourHistorySchema(
                tour_id=loaded_squad_tour.tour_id,
                tour_number=tour_number,
                points=loaded_squad_tour.points,
                penalty_points=loaded_squad_tour.penalty_points,
                used_boost=loaded_squad_tour.used_boost,
                captain_id=loaded_squad_tour.captain_id,
                vice_captain_id=loaded_squad_tour.vice_captain_id,
                budget=loaded_squad_tour.budget,
                replacements=loaded_squad_tour.replacements,
                is_finalized=loaded_squad_tour.is_finalized,
                main_players=main_players_data,
                bench_players=bench_players_data,
            ))
    
    return result


@router.get("/all", response_model=List[SquadTourHistorySchema])
async def get_all_squad_tours() -> List[SquadTourHistorySchema]:
    """Get all SquadTours for all squads and all tours."""
    from app.database import async_session_maker
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload, selectinload
    from app.squad_tours.models import SquadTour
    from app.players.models import Player
    
    async with async_session_maker() as session:
        stmt = (
            select(SquadTour)
            .options(
                joinedload(SquadTour.tour),
                selectinload(SquadTour.main_players).joinedload(Player.team),
                selectinload(SquadTour.bench_players).joinedload(Player.team)
            )
            .order_by(SquadTour.squad_id, SquadTour.tour_id)
        )
        result_db = await session.execute(stmt)
        squad_tours = result_db.unique().scalars().all()
        
        result = []
        opponent_maps: dict[int, dict[int, tuple[str, bool]]] = {}
        for squad_tour in squad_tours:
            # Получаем отображение team_id -> (opponent_name, is_home) для этого тура (кешируем по tour_id)
            if squad_tour.tour_id not in opponent_maps:
                opponent_maps[squad_tour.tour_id] = await _get_opponent_map_for_tour(session, squad_tour.tour_id)
            opponent_map = opponent_maps[squad_tour.tour_id]

            main_players_data = []
            for player in squad_tour.main_players:
                total_points = await SquadService._get_player_total_points(session, player.id)
                tour_points = await SquadService._get_player_tour_points(session, player.id, squad_tour.tour_id)
                opponent_info = opponent_map.get(player.team_id)
                
                main_players_data.append({
                    "id": player.id,
                    "name": player.name,
                    "position": player.position,
                    "team_id": player.team_id,
                    "team_name": player.team.name if player.team else "",
                    "team_logo": player.team.logo if player.team else None,
                    "market_value": player.market_value,
                    "photo": player.photo,
                    "total_points": total_points,
                    "tour_points": tour_points,
                    "next_opponent_team_name": opponent_info[0] if opponent_info else None,
                    "next_opponent_is_home": opponent_info[1] if opponent_info else None,
                })
            
            bench_players_data = []
            for player in squad_tour.bench_players:
                total_points = await SquadService._get_player_total_points(session, player.id)
                tour_points = await SquadService._get_player_tour_points(session, player.id, squad_tour.tour_id)
                opponent_info = opponent_map.get(player.team_id)
                
                bench_players_data.append({
                    "id": player.id,
                    "name": player.name,
                    "position": player.position,
                    "team_id": player.team_id,
                    "team_name": player.team.name if player.team else "",
                    "team_logo": player.team.logo if player.team else None,
                    "market_value": player.market_value,
                    "photo": player.photo,
                    "total_points": total_points,
                    "tour_points": tour_points,
                    "next_opponent_team_name": opponent_info[0] if opponent_info else None,
                    "next_opponent_is_home": opponent_info[1] if opponent_info else None,
                })
            
            result.append(SquadTourHistorySchema(
                tour_id=squad_tour.tour_id,
                tour_number=squad_tour.tour.number if squad_tour.tour else 0,
                points=squad_tour.points,
                penalty_points=squad_tour.penalty_points,
                used_boost=squad_tour.used_boost,
                captain_id=squad_tour.captain_id,
                vice_captain_id=squad_tour.vice_captain_id,
                budget=squad_tour.budget,
                replacements=squad_tour.replacements,
                is_finalized=squad_tour.is_finalized,
                main_players=main_players_data,
                bench_players=bench_players_data,
            ))
        
        return result


@router.post("/squad/{squad_id}/replace_players", response_model=SquadTourReplacePlayersResponseSchema)
async def replace_players(
    squad_id: int,
    captain_id: Optional[int] = None,
    vice_captain_id: Optional[int] = None,
    payload: SquadTourUpdatePlayersSchema = None,
    user: User = Depends(get_current_user),
) -> SquadTourReplacePlayersResponseSchema:
    """Replace players in squad for next available tour.
    
    New architecture: All changes are made to SquadTour, not Squad.
    Returns SquadTour with updated state.
    """
    payload = payload or SquadTourUpdatePlayersSchema()
    main_player_ids = payload.main_player_ids or []
    bench_player_ids = payload.bench_player_ids or []

    result = await SquadService.replace_players(
        squad_id=squad_id,
        captain_id=captain_id,
        vice_captain_id=vice_captain_id,
        new_main_players=main_player_ids,
        new_bench_players=bench_player_ids,
    )
    
    squad_tour = result["squad_tour"]
    
    # Log the result for debugging
    logger.info(
        f"Squad {squad_id} tour {squad_tour.tour_id} transfers completed: "
        f"transfers={result['transfers_applied']}, "
        f"free={result['free_transfers_used']}, "
        f"paid={result['paid_transfers']}, "
        f"penalty={result['penalty']}, "
        f"remaining_replacements={squad_tour.replacements}"
    )
    
    # Convert SquadTour to response format
    from app.tours.services import TourService
    tour = await TourService.find_one_or_none(id=squad_tour.tour_id)
    
    return SquadTourReplacePlayersResponseSchema(
        status="success",
        message="Players replaced successfully",
        remaining_replacements=squad_tour.replacements,
        squad_tour=SquadTourHistorySchema(
            tour_id=squad_tour.tour_id,
            tour_number=tour.number if tour else 0,
            points=squad_tour.points,
            penalty_points=squad_tour.penalty_points,
            used_boost=squad_tour.used_boost,
            captain_id=squad_tour.captain_id,
            vice_captain_id=squad_tour.vice_captain_id,
            budget=squad_tour.budget,
            replacements=squad_tour.replacements,
            is_finalized=squad_tour.is_finalized,
            main_players=[],  # Will be populated by frontend
            bench_players=[],
        ),
        transfers_applied=result["transfers_applied"],
        free_transfers_used=result["free_transfers_used"],
        paid_transfers=result["paid_transfers"],
        penalty=result["penalty"],
    )


@router.get("/squad/{squad_id}/replacement_info", response_model=ReplacementInfoSchema)
async def get_replacement_info(
    squad_id: int,
    user: User = Depends(get_current_user)
) -> ReplacementInfoSchema:
    """Get replacement info for squad's current/next open tour."""
    return await SquadService.get_replacement_info(squad_id)

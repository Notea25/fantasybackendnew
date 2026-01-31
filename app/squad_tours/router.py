from fastapi import APIRouter, HTTPException
from typing import List

from app.squad_tours.schemas import SquadTourHistorySchema
from app.squad_tours.services import SquadTourService
from app.squads.services import SquadService
from app.utils.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/squad_tours", tags=["Squad Tours"])


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
        main_players_data = []
        for player in squad_tour.main_players:
            total_points = await SquadService._get_player_total_points(session, player.id)
            tour_points = await SquadService._get_player_tour_points(session, player.id, tour_id)
            
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
            })
        
        bench_players_data = []
        for player in squad_tour.bench_players:
            total_points = await SquadService._get_player_total_points(session, player.id)
            tour_points = await SquadService._get_player_tour_points(session, player.id, tour_id)
            
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
                })
            
            bench_players_data = []
            for player in loaded_squad_tour.bench_players:
                total_points = await SquadService._get_player_total_points(session, player.id)
                tour_points = await SquadService._get_player_tour_points(session, player.id, tour_id)
                
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
        for squad_tour in squad_tours:
            main_players_data = []
            for player in squad_tour.main_players:
                total_points = await SquadService._get_player_total_points(session, player.id)
                tour_points = await SquadService._get_player_tour_points(session, player.id, squad_tour.tour_id)
                
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
                })
            
            bench_players_data = []
            for player in squad_tour.bench_players:
                total_points = await SquadService._get_player_total_points(session, player.id)
                tour_points = await SquadService._get_player_tour_points(session, player.id, squad_tour.tour_id)
                
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

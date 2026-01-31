import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.database import async_session_maker
from app.squad_tours.models import SquadTour
from app.utils.base_service import BaseService

logger = logging.getLogger(__name__)


class SquadTourService(BaseService):
    """Service for SquadTour operations.
    
    Handles operations specific to SquadTour entity.
    Complex operations involving both Squad and SquadTour remain in SquadService.
    """
    model = SquadTour

    @classmethod
    async def find_by_squad_and_tour(
        cls,
        squad_id: int,
        tour_id: int,
        with_players: bool = False
    ) -> Optional[SquadTour]:
        """Find SquadTour by squad_id and tour_id.
        
        Args:
            squad_id: Squad ID
            tour_id: Tour ID
            with_players: Whether to load player relationships
            
        Returns:
            SquadTour or None if not found
        """
        async with async_session_maker() as session:
            stmt = select(SquadTour).where(
                SquadTour.squad_id == squad_id,
                SquadTour.tour_id == tour_id
            )
            
            if with_players:
                from app.players.models import Player
                stmt = stmt.options(
                    selectinload(SquadTour.main_players).joinedload(Player.team),
                    selectinload(SquadTour.bench_players).joinedload(Player.team)
                )
            
            result = await session.execute(stmt)
            return result.scalars().first()

    @classmethod
    async def find_all_by_squad(
        cls,
        squad_id: int,
        with_players: bool = False,
        order_by_tour: bool = True
    ) -> list[SquadTour]:
        """Find all SquadTours for a squad.
        
        Args:
            squad_id: Squad ID
            with_players: Whether to load player relationships
            order_by_tour: Whether to order by tour_id ascending
            
        Returns:
            List of SquadTours
        """
        async with async_session_maker() as session:
            stmt = select(SquadTour).where(SquadTour.squad_id == squad_id)
            
            if with_players:
                from app.players.models import Player
                stmt = stmt.options(
                    selectinload(SquadTour.main_players).joinedload(Player.team),
                    selectinload(SquadTour.bench_players).joinedload(Player.team)
                )
            
            if order_by_tour:
                stmt = stmt.order_by(SquadTour.tour_id.asc())
            
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def find_all_by_tour(
        cls,
        tour_id: int,
        finalized_only: bool = False
    ) -> list[SquadTour]:
        """Find all SquadTours for a tour.
        
        Args:
            tour_id: Tour ID
            finalized_only: Whether to return only finalized tours
            
        Returns:
            List of SquadTours
        """
        async with async_session_maker() as session:
            stmt = select(SquadTour).where(SquadTour.tour_id == tour_id)
            
            if finalized_only:
                stmt = stmt.where(SquadTour.is_finalized == True)
            
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def get_total_points_for_squad(cls, squad_id: int) -> int:
        """Get total points earned across all tours for a squad.
        
        Args:
            squad_id: Squad ID
            
        Returns:
            Total points (excluding penalties)
        """
        async with async_session_maker() as session:
            stmt = select(
                func.coalesce(func.sum(SquadTour.points), 0)
            ).where(SquadTour.squad_id == squad_id)
            
            result = await session.execute(stmt)
            return result.scalar() or 0

    @classmethod
    async def get_total_penalty_for_squad(cls, squad_id: int) -> int:
        """Get total penalty points across all tours for a squad.
        
        Args:
            squad_id: Squad ID
            
        Returns:
            Total penalty points
        """
        async with async_session_maker() as session:
            stmt = select(
                func.coalesce(func.sum(SquadTour.penalty_points), 0)
            ).where(SquadTour.squad_id == squad_id)
            
            result = await session.execute(stmt)
            return result.scalar() or 0

import logging
from typing import Optional, List

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.player_statuses.models import PlayerStatus
from app.player_statuses.schemas import PlayerStatusCreateSchema, PlayerStatusUpdateSchema
from app.utils.base_service import BaseService

logger = logging.getLogger(__name__)


class PlayerStatusService(BaseService):
    model = PlayerStatus

    @classmethod
    async def get_by_id(cls, status_id: int) -> Optional[PlayerStatus]:
        """Get player status by ID."""
        logger.debug(f"Getting status with ID: {status_id}")
        return await cls.find_one_or_none(id=status_id)

    @classmethod
    async def get_player_statuses(cls, player_id: int) -> List[PlayerStatus]:
        """Get all statuses for a player."""
        logger.debug(f"Getting all statuses for player ID: {player_id}")
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .where(cls.model.player_id == player_id)
                .order_by(cls.model.tour_start.desc())
            )
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_active_status_for_tour(
        cls, player_id: int, tour_number: int
    ) -> List[PlayerStatus]:
        """Get active statuses for a player in a specific tour."""
        logger.debug(
            f"Getting active statuses for player {player_id} in tour {tour_number}"
        )
        async with async_session_maker() as session:
            query = select(cls.model).where(
                cls.model.player_id == player_id,
                cls.model.tour_start <= tour_number,
                or_(
                    cls.model.tour_end >= tour_number,
                    cls.model.tour_end.is_(None)  # Indefinite status
                ),
            )
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def add_status(
        cls, player_id: int, status_data: PlayerStatusCreateSchema
    ) -> PlayerStatus:
        """Create a new player status."""
        logger.debug(f"Creating status for player {player_id}: {status_data}")
        async with async_session_maker() as session:
            try:
                status = cls.model(
                    player_id=player_id, **status_data.model_dump()
                )
                session.add(status)
                await session.commit()
                await session.refresh(status)
                logger.debug(f"Status created: {status.id}")
                return status
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating status: {str(e)}", exc_info=True)
                raise

    @classmethod
    async def update_status(
        cls, status_id: int, status_data: PlayerStatusUpdateSchema
    ) -> Optional[PlayerStatus]:
        """Update an existing player status."""
        logger.debug(f"Updating status {status_id}: {status_data}")
        async with async_session_maker() as session:
            try:
                status = await session.get(cls.model, status_id)
                if not status:
                    logger.debug(f"Status not found: {status_id}")
                    return None

                for key, value in status_data.model_dump(exclude_unset=True).items():
                    setattr(status, key, value)

                await session.commit()
                await session.refresh(status)
                logger.debug(f"Status updated: {status_id}")
                return status
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating status: {str(e)}", exc_info=True)
                raise

    @classmethod
    async def delete_status(cls, status_id: int) -> bool:
        """Delete a player status."""
        logger.debug(f"Deleting status {status_id}")
        async with async_session_maker() as session:
            try:
                status = await session.get(cls.model, status_id)
                if not status:
                    logger.debug(f"Status not found: {status_id}")
                    return False

                await session.delete(status)
                await session.commit()
                logger.debug(f"Status deleted: {status_id}")
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting status: {str(e)}", exc_info=True)
                raise

    @classmethod
    async def get_players_with_status_in_tour(
        cls, tour_number: int, status_type: Optional[str] = None
    ) -> List[int]:
        """Get list of player IDs with specific status (or any status) in a tour."""
        logger.debug(
            f"Getting players with status '{status_type}' in tour {tour_number}"
        )
        async with async_session_maker() as session:
            query = select(cls.model.player_id).where(
                cls.model.tour_start <= tour_number,
                or_(
                    cls.model.tour_end >= tour_number,
                    cls.model.tour_end.is_(None)
                ),
            )
            
            if status_type:
                query = query.where(cls.model.status_type == status_type)
            
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_all_statuses_for_tour(
        cls, tour_number: int, status_type: Optional[str] = None
    ) -> List[PlayerStatus]:
        """Get all active player statuses for a specific tour."""
        logger.debug(
            f"Getting all statuses for tour {tour_number}, status_type: {status_type}"
        )
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .where(
                    cls.model.tour_start <= tour_number,
                    or_(
                        cls.model.tour_end >= tour_number,
                        cls.model.tour_end.is_(None)
                    ),
                )
                .options(selectinload(cls.model.player))
                .order_by(cls.model.player_id)
            )
            
            if status_type:
                query = query.where(cls.model.status_type == status_type)
            
            result = await session.execute(query)
            return result.scalars().all()

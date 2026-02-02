from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.player_statuses.schemas import (
    PlayerStatusSchema,
    PlayerStatusCreateSchema,
    PlayerStatusUpdateSchema,
    VALID_STATUS_TYPES,
)
from app.player_statuses.services import PlayerStatusService

router = APIRouter(prefix="/player-statuses", tags=["Player Statuses"])


@router.get("/{status_id}", response_model=PlayerStatusSchema)
async def get_status(status_id: int):
    """Get player status by ID."""
    status = await PlayerStatusService.get_by_id(status_id)
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Status with ID {status_id} not found",
        )
    return status


@router.get("/players/{player_id}/statuses", response_model=List[PlayerStatusSchema])
async def get_player_statuses(player_id: int):
    """Get all statuses for a player."""
    statuses = await PlayerStatusService.get_player_statuses(player_id)
    return statuses


@router.get("/tour/{tour_number}", response_model=List[PlayerStatusSchema])
async def get_all_statuses_for_tour(
    tour_number: int,
    status_type: Optional[str] = Query(None, description="Filter by status type")
):
    """Get all active player statuses for a specific tour."""
    # Validate status type if provided
    if status_type and status_type not in VALID_STATUS_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status type. Must be one of: {', '.join(VALID_STATUS_TYPES)}",
        )
    
    statuses = await PlayerStatusService.get_all_statuses_for_tour(
        tour_number, status_type
    )
    return statuses


@router.get(
    "/players/{player_id}/statuses/tour/{tour_number}",
    response_model=List[PlayerStatusSchema],
)
async def get_player_status_for_tour(player_id: int, tour_number: int):
    """Get active statuses for a player in a specific tour."""
    statuses = await PlayerStatusService.get_active_status_for_tour(
        player_id, tour_number
    )
    return statuses


@router.post(
    "/players/{player_id}/statuses",
    response_model=PlayerStatusSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_player_status(
    player_id: int, status_data: PlayerStatusCreateSchema
):
    """Create a new player status."""
    # Validate status type
    if status_data.status_type not in VALID_STATUS_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status type. Must be one of: {', '.join(VALID_STATUS_TYPES)}",
        )
    
    # Validate tour range
    if status_data.tour_end is not None and status_data.tour_end < status_data.tour_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tour_end must be greater than or equal to tour_start",
        )
    
    new_status = await PlayerStatusService.add_status(player_id, status_data)
    return new_status


@router.put("/{status_id}", response_model=PlayerStatusSchema)
async def update_player_status(
    status_id: int, status_data: PlayerStatusUpdateSchema
):
    """Update an existing player status."""
    # Validate status type if provided
    if (
        status_data.status_type is not None
        and status_data.status_type not in VALID_STATUS_TYPES
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status type. Must be one of: {', '.join(VALID_STATUS_TYPES)}",
        )
    
    updated_status = await PlayerStatusService.update_status(status_id, status_data)
    if not updated_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Status with ID {status_id} not found",
        )
    return updated_status


@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player_status(status_id: int):
    """Delete a player status."""
    deleted = await PlayerStatusService.delete_status(status_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Status with ID {status_id} not found",
        )
    return None
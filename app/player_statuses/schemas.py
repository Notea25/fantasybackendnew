from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Status type constants
STATUS_RED_CARD = "red_card"
STATUS_INJURED = "injured"
STATUS_LEFT_LEAGUE = "left_league"

VALID_STATUS_TYPES = [STATUS_RED_CARD, STATUS_INJURED, STATUS_LEFT_LEAGUE]


class PlayerStatusSchema(BaseModel):
    """Full player status information."""
    id: int
    player_id: int
    status_type: str
    tour_start: int
    tour_end: Optional[int] = None
    
    class Config:
        from_attributes = True


class PlayerStatusCreateSchema(BaseModel):
    """Schema for creating a new player status."""
    status_type: str = Field(..., description="Status type: red_card, injured, or left_league")
    tour_start: int = Field(..., ge=1, description="Starting tour number")
    tour_end: Optional[int] = Field(None, ge=1, description="Ending tour number (null for indefinite)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status_type": "injured",
                "tour_start": 5,
                "tour_end": 7
            }
        }


class PlayerStatusUpdateSchema(BaseModel):
    """Schema for updating an existing player status."""
    status_type: Optional[str] = Field(None, description="Status type: red_card, injured, or left_league")
    tour_start: Optional[int] = Field(None, ge=1, description="Starting tour number")
    tour_end: Optional[int] = Field(None, ge=1, description="Ending tour number (null for indefinite)")

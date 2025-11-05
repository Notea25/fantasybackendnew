from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional

class MatchCreateSchema(BaseModel):
    id: int
    date: datetime
    status: str
    duration: Optional[int] = None
    league_id: int
    home_team_id: int
    away_team_id: int
    home_team_score: Optional[int] = None
    away_team_score: Optional[int] = None
    home_team_penalties: Optional[int] = None
    away_team_penalties: Optional[int] = None

    @field_validator('status', mode='before')
    def set_default_status(cls, value):
        return value if value else "Not Started"

class MatchSchema(MatchCreateSchema):
    id: int

    class Config:
        from_attributes = True

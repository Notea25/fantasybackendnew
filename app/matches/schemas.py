from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class MatchSchema(BaseModel):
    id: int
    date: datetime
    status: str
    duration: Optional[int]
    league_id: int
    home_team_id: int
    away_team_id: int
    home_team_score: Optional[int]
    away_team_score: Optional[int]
    home_team_penalties: Optional[int]
    away_team_penalties: Optional[int]

    class Config:
        from_attributes = True

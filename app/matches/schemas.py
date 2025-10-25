from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Match(BaseModel):
    id: int
    date: datetime
    status: str
    league_id: int
    home_team_id: int
    away_team_id: int
    home_team_score: Optional[int] = None
    away_team_score: Optional[int] = None
    home_team_penalties: Optional[int] = None
    away_team_penalties: Optional[int] = None
    duration: Optional[int] = None

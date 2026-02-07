from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional

class MatchCreateSchema(BaseModel):
    id: int
    date: datetime
    is_finished: bool = False
    finished_at: Optional[datetime] = None
    duration: Optional[int] = None
    league_id: int
    home_team_id: int
    away_team_id: int
    home_team_score: Optional[int] = None
    away_team_score: Optional[int] = None
    home_team_penalties: Optional[int] = None
    away_team_penalties: Optional[int] = None

class MatchSchema(MatchCreateSchema):
    id: int

    class Config:
        from_attributes = True

class MatchInTourSchema(BaseModel):
    match_id: int
    is_home: bool
    opponent_team_id: int
    opponent_team_name: str
    opponent_team_logo: Optional[str]
    player_points: Optional[int] = None

    class Config:
        from_attributes = True
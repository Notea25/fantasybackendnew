from typing import Optional

from pydantic import BaseModel

class PlayerSchema(BaseModel):
    id: int
    name: str
    age: Optional[int]
    number: Optional[int]
    position: Optional[str]
    photo: Optional[str]
    team_id: int
    market_value: Optional[int]
    sport: int
    league_id: int

    class Config:
        from_attributes = True

class PlayerBaseInfoSchema(BaseModel):
    id: int
    name: str
    photo: Optional[str]
    team_id: int
    team_name: str
    team_logo: Optional[str]
    position: Optional[str]

    class Config:
        from_attributes = True

class PlayerExtendedInfoSchema(BaseModel):
    total_players_in_league: int
    market_value_rank: int
    avg_points_all_matches: float
    avg_points_all_matches_rank: int
    avg_points_last_5_matches: float
    avg_points_last_5_matches_rank: int
    squad_presence_percentage: float
    squad_presence_rank: int

    class Config:
        from_attributes = True
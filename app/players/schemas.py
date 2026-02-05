from typing import Optional, List

from pydantic import BaseModel, field_validator

from app.tours.schemas import TourWithMatchesSchema


class PlayerSchema(BaseModel):
    id: int
    name: str
    name_rus: Optional[str] = None
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

class PlayerWithTotalPointsSchema(BaseModel):
    id: int
    name: str
    name_rus: Optional[str] = None
    team_id: int
    team_name: str
    team_name_rus: Optional[str] = None
    team_logo: Optional[str]
    position: Optional[str]
    market_value: Optional[int]
    points: int

    @field_validator('points', mode='before')
    def set_default_points(cls, value):
        return value if value is not None else 0

    class Config:
        from_attributes = True

class PlayerBaseInfoSchema(BaseModel):
    id: int
    name: str
    name_rus: Optional[str] = None
    photo: Optional[str]
    team_id: int
    team_name: str
    team_name_rus: Optional[str] = None
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

class PlayerFullInfoSchema(BaseModel):
    base_info: PlayerBaseInfoSchema
    extended_info: PlayerExtendedInfoSchema
    last_3_tours: list[TourWithMatchesSchema]
    next_3_tours: list[TourWithMatchesSchema]

    class Config:
        from_attributes = True
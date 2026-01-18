from pydantic import BaseModel
from typing import List, Optional

class TourSchema(BaseModel):
    id: int
    number: int

class SquadSchema(BaseModel):
    id: int
    name: str

class UserLeagueSchema(BaseModel):
    id: int
    name: str
    league_id: int
    creator_id: int
    tours: List[TourSchema] = []
    squads: List[SquadSchema] = []

    class Config:
        from_attributes = True

class UserLeagueWithStatsSchema(BaseModel):
    user_league_id: int
    league_name: str
    total_players: int
    squad_place: int
    is_creator: bool
    squad_id: int
    squad_name: str

    class Config:
        from_attributes = True

class UserLeagueCreateSchema(BaseModel):
    name: str
    league_id: int


    class Config:
        from_attributes = True
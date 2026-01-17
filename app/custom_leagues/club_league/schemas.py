from pydantic import BaseModel
from typing import Optional, List

class TourSchema(BaseModel):
    id: int
    number: int

    class Config:
        from_attributes = True

class SquadSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ClubLeagueSchema(BaseModel):
    id: int
    name: str
    league_id: int
    team_id: int
    tours: List[TourSchema] = []
    squads: List[SquadSchema] = []

    class Config:
        from_attributes = True

class ClubLeagueListSchema(BaseModel):
    id: int
    name: str
    league_id: int
    team_id: int

    class Config:
        from_attributes = True
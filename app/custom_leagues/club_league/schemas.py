from pydantic import BaseModel
from typing import List

class TourSchema(BaseModel):
    id: int
    name: str

class SquadSchema(BaseModel):
    id: int
    name: str

class ClubLeagueSchema(BaseModel):
    id: int
    name: str
    league_id: int
    team_id: int
    tours: List[TourSchema] = []
    squads: List[SquadSchema] = []

    class Config:
        from_attributes = True

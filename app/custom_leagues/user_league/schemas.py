from pydantic import BaseModel
from typing import List

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

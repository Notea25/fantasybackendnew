from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TourSchema(BaseModel):
    id: int
    number: int

class SquadSchema(BaseModel):
    id: int
    name: str

class CommercialLeagueSchema(BaseModel):
    id: int
    name: str
    league_id: int
    prize: Optional[str]
    logo: Optional[str]
    winner_id: Optional[int]
    winner_name: Optional[str]
    registration_start: Optional[datetime]
    registration_end: Optional[datetime]
    tours: List[TourSchema] = []
    squads: List[SquadSchema] = []

    class Config:
        from_attributes = True


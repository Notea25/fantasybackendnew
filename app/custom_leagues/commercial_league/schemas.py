from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class TourSchema(BaseModel):
    id: int
    number: int

    class Config:
        from_attributes = True


class SquadSchema(BaseModel):
    squad_id: int
    squad_name: Optional[str] = None

    class Config:
        from_attributes = True


class CommercialLeagueSchema(BaseModel):
    id: int
    name: str
    league_id: int
    prize: Optional[str]
    logo: Optional[str]
    winner_id: Optional[int]
    winner_name: Optional[str] = None
    registration_start: Optional[datetime]
    registration_end: Optional[datetime]
    tours: List[TourSchema] = []
    squads: List[dict] = []

    class Config:
        from_attributes = True

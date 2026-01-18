from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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

    class Config:
        from_attributes = True
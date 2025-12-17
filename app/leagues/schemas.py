from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class LeagueSchema(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    country: Optional[str] = None
    sport: str

    class Config:
        from_attributes = True

class LeagueMainPageSchema(LeagueSchema):
    all_squads_quantity: Optional[int] = None
    your_place: Optional[int] = None
    deadline: Optional[datetime] = None
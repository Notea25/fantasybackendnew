from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CommercialLeagueSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    league_id: int
    prize: Optional[str]
    logo: Optional[str]
    is_public: bool
    registration_start: Optional[datetime]
    registration_end: Optional[datetime]

    class Config:
        from_attributes = True

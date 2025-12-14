from typing import Optional

from pydantic import BaseModel

class LeagueSchema(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    sport: str

    class Config:
        from_attributes = True

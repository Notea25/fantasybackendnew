from pydantic import BaseModel
from enum import Enum

class CustomLeagueType(str, Enum):
    COMMERCIAL = "Commercial"
    USER = "User"
    CLUB = "Club"

class CustomLeagueBase(BaseModel):
    name: str
    description: str | None = None
    league_id: int
    type: CustomLeagueType
    is_public: bool = False
    invitation_only: bool = False

class CustomLeagueCreate(CustomLeagueBase):
    pass

class CustomLeague(CustomLeagueBase):
    id: int

    class Config:
        from_attributes = True

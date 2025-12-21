from pydantic import BaseModel
from datetime import datetime
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
    registration_start: datetime | None = None
    registration_end: datetime | None = None

class CustomLeagueCreate(CustomLeagueBase):
    pass

class CustomLeague(CustomLeagueBase):
    id: int
    creator_id: int | None = None

    class Config:
        from_attributes = True

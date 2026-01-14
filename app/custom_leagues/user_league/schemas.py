from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserLeagueSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    league_id: int
    is_public: bool
    invitation_only: bool
    creator_id: int
    registration_start: Optional[datetime]
    registration_end: Optional[datetime]

    class Config:
        from_attributes = True

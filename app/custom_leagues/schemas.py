from typing import Optional

from pydantic import BaseModel, validator
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

class CustomLeagueCreate(BaseModel):
    name: str
    description: Optional[str] = None
    league_id: int
    type: str
    is_public: bool = False
    invitation_only: bool = False
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None

    @validator("registration_start", "registration_end", pre=True)
    def parse_and_remove_timezone(cls, value):
        if isinstance(value, str):
            # Если значение — строка, преобразуем её в datetime
            value = datetime.fromisoformat(value)
        if value and hasattr(value, 'tzinfo') and value.tzinfo:
            # Удаляем временную зону, если она есть
            value = value.replace(tzinfo=None)
        return value

class CustomLeague(CustomLeagueBase):
    id: int
    creator_id: int | None = None

    class Config:
        from_attributes = True

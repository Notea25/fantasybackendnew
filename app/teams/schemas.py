from typing import Optional

from pydantic import BaseModel


class TeamSchema(BaseModel):
    id: int
    name: str
    name_rus: str
    logo: Optional[str] = None
    league_id: int

    class Config:
        from_attributes = True
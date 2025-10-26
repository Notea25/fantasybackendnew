from pydantic import BaseModel

class TeamSchema(BaseModel):
    id: int
    name: str
    league_id: int

    class Config:
        from_attributes = True

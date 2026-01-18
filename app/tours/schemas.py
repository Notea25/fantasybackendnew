from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import datetime

from app.matches.schemas import MatchInTourSchema


class TourRead(BaseModel):
    id: int
    number: int
    league_id: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    deadline: Optional[datetime]

    @field_serializer("start_date", "end_date", "deadline")
    def serialize_dates(self, date: Optional[datetime], _info):
        if date is None:
            return None
        return date.isoformat()
    model_config = ConfigDict(from_attributes=True)

class TourWithMatchesSchema(BaseModel):
    tour_id: int
    tour_number: int
    matches: list[MatchInTourSchema]

    class Config:
        from_attributes = True


class TourReadWithType(BaseModel):
    id: int
    number: int
    league_id: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    deadline: Optional[datetime]
    type: Literal["previous", "current", "next"]

    @field_serializer("start_date", "end_date", "deadline")
    def serialize_dates(self, date: Optional[datetime], _info):
        if date is None:
            return None
        return date.isoformat()
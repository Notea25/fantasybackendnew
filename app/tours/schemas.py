from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import datetime


class TourBase(BaseModel):
    number: int
    league_id: int
    start_date: datetime
    end_date: datetime
    deadline: datetime


class TourRead(BaseModel):
    id: int
    name: str
    league_id: int
    matches: list[int] = []
    start_date: datetime
    end_date: datetime

    @field_serializer("start_date", "end_date")
    def serialize_dates(self, date: datetime, _info):
        return date.isoformat()

    model_config = ConfigDict(from_attributes=True)

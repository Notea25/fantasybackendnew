from typing import List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class TourRead(BaseModel):
    id: int
    name: str
    league_id: int
    start_date: datetime
    end_date: datetime
    matches: List[int] = []

    model_config = ConfigDict(from_attributes=True)

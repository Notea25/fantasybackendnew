from typing import Optional
from datetime import date
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: int
    username: str
    photo_url: Optional[str]
    emblem_url: Optional[str]
    birth_date: Optional[date]

    class Config:
        from_attributes = True

class UserCreateSchema(BaseModel):
    username: str
    photo_url: Optional[str] = None
    emblem_url: Optional[str] = None
    birth_date: Optional[date] = None

class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    photo_url: Optional[str] = None
    emblem_url: Optional[str] = None
    birth_date: Optional[date] = None

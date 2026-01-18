from typing import Optional

from pydantic import BaseModel


class UserSchema(BaseModel):
    id: int
    username: str
    photo_url: Optional[str]
    emblem_url: Optional[str]

    class Config:
        from_attributes = True


class UserCreateSchema(BaseModel):
    username: str
    photo_url: Optional[str] = None
    emblem_url: Optional[str] = None


class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    photo_url: Optional[str] = None
    emblem_url: Optional[str] = None
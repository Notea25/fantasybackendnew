from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(..., example="user123456")
    photo_url: Optional[str] = Field(None, example="https://example.com/photo.jpg")
    emblem_url: Optional[str] = Field(None, example="https://example.com/emblem.png")


class UserCreate(BaseModel):
    id: int = Field(..., example=123456789)
    photo_url: Optional[str] = Field(None, example="https://example.com/photo.jpg")
    emblem_url: Optional[str] = Field(None, example="https://example.com/emblem.png")

    class Config:
        extra = "allow"  # Разрешаем дополнительные поля


class User(UserBase):
    id: int = Field(..., example=123456789)

    class Config:
        from_attributes = True

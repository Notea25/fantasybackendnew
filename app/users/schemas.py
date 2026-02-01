from typing import Optional
from datetime import date, datetime

from pydantic import BaseModel


class UserSchema(BaseModel):
    id: int
    username: str
    tg_username: Optional[str] = None
    photo_url: Optional[str]
    birth_date: Optional[date] = None
    registration_date: Optional[datetime] = None
    referrer_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserReferrerSchema(BaseModel):
    """Schema for referrer information."""
    id: int
    username: str
    
    class Config:
        from_attributes = True


class UserReferralSchema(BaseModel):
    """Schema for referral (invited user) information."""
    id: int
    username: str
    registration_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserReferralsResponse(BaseModel):
    """Paginated response for user referrals."""
    total: int
    page: int
    page_size: int
    referrals: list[UserReferralSchema]


class UserCreateSchema(BaseModel):
    username: str
    tg_username: Optional[str] = None
    photo_url: Optional[str] = None
    birth_date: Optional[date] = None
    referrer_id: Optional[int] = None


class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    tg_username: Optional[str] = None
    photo_url: Optional[str] = None
    birth_date: Optional[date] = None

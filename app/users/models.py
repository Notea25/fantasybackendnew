from typing import Optional
from datetime import date, datetime

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    tg_username: Mapped[Optional[str]] = mapped_column(nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    registration_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    referrer_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    squads: Mapped[list["Squad"]] = relationship(back_populates="user")
    user_leagues: Mapped[list["UserLeague"]] = relationship(
        back_populates="creator"
    )
    
    # Referral relationships
    referrer: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[referrer_id],
        back_populates="referrals"
    )
    referrals: Mapped[list["User"]] = relationship(
        "User",
        foreign_keys=[referrer_id],
        back_populates="referrer"
    )

    def __repr__(self):
        return f"User {self.username}"

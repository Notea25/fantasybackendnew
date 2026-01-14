from sqlalchemy import ForeignKey,DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from datetime import datetime

class UserLeague(Base):
    __tablename__ = "user_leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    is_public: Mapped[bool] = mapped_column(default=False)
    invitation_only: Mapped[bool] = mapped_column(default=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    registration_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    registration_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    league: Mapped["League"] = relationship(back_populates="user_leagues")
    creator: Mapped["User"] = relationship(back_populates="user_leagues")

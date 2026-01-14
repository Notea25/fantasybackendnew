from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from datetime import datetime

class CommercialLeague(Base):
    __tablename__ = "commercial_leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    prize: Mapped[str] = mapped_column(nullable=True)
    logo: Mapped[str] = mapped_column(nullable=True)
    is_public: Mapped[bool] = mapped_column(default=True)
    winner_id: Mapped[int] = mapped_column(ForeignKey("squads.id"), nullable=True)

    registration_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    registration_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    league: Mapped["League"] = relationship(back_populates="commercial_leagues")
    winner: Mapped["Squad"] = relationship(foreign_keys=[winner_id])

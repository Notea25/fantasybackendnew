from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey,  DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str]
    duration: Mapped[Optional[int]]
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    home_team_score: Mapped[Optional[int]]
    away_team_score: Mapped[Optional[int]]
    home_team_penalties: Mapped[Optional[int]]
    away_team_penalties: Mapped[Optional[int]]


    league = relationship("League", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")

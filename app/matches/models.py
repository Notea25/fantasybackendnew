from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.tours.models import tour_matches_association

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

    player_stats: Mapped[list["PlayerMatchStats"]] = relationship(back_populates="match")
    league: Mapped["League"] = relationship(back_populates="matches")
    home_team: Mapped["Team"] = relationship(foreign_keys=[home_team_id], back_populates="home_matches")
    away_team: Mapped["Team"] = relationship(foreign_keys=[away_team_id], back_populates="away_matches")
    tours: Mapped[list["Tour"]] = relationship(
        secondary=tour_matches_association,
        back_populates="matches"
    )

    def __str__(self):
        return f'{self.home_team_id}{self.away_team_id}'
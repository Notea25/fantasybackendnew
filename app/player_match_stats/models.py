from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class PlayerMatchStats(Base):
    __tablename__ = "player_match_stats"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    position: Mapped[str] = mapped_column(default="Unknown", nullable=True)
    goals_total: Mapped[int] = mapped_column(default=0, nullable=True)
    assists: Mapped[int] = mapped_column(default=0, nullable=True)
    yellow_cards: Mapped[int] = mapped_column(default=0, nullable=True)
    red_cards: Mapped[int] = mapped_column(default=0, nullable=True)
    minutes_played: Mapped[int] = mapped_column(default=0, nullable=True)
    points: Mapped[int] = mapped_column(default=0, nullable=True)

    player: Mapped["Player"] = relationship(back_populates="match_stats")
    match: Mapped["Match"] = relationship()
    team: Mapped["Team"] = relationship()
    league: Mapped["League"] = relationship()

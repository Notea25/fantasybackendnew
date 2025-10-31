from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class PlayerStats(Base):
    __tablename__ = "player_stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    season: Mapped[int]

    appearances: Mapped[int] = mapped_column(default=0, nullable=True)
    lineups: Mapped[int] = mapped_column(default=0, nullable=True)
    minutes_played: Mapped[int] = mapped_column(default=0, nullable=True)
    position: Mapped[str] = mapped_column(default="Unknown", nullable=True)

    goals_total: Mapped[int] = mapped_column(default=0, nullable=True)
    assists: Mapped[int] = mapped_column(default=0, nullable=True)
    yellow_cards: Mapped[int] = mapped_column(default=0, nullable=True)
    yellow_red_cards: Mapped[int] = mapped_column(default=0, nullable=True)
    red_cards: Mapped[int] = mapped_column(default=0, nullable=True)

    player: Mapped["Player"] = relationship(back_populates="stats")
    league: Mapped["League"] = relationship()
    team: Mapped["Team"] = relationship()

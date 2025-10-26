from sqlalchemy import Boolean, ForeignKey, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class PlayerMatchStats(Base):
    __tablename__ = "player_match_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    position: Mapped[str]
    minutes_played: Mapped[int] = mapped_column(Integer, default=0)
    is_substitute: Mapped[bool] = mapped_column(Boolean, default=False)
    yellow_cards: Mapped[int] = mapped_column(Integer, default=0)
    yellow_red_cards: Mapped[int] = mapped_column(Integer, default=0)
    red_cards: Mapped[int] = mapped_column(Integer, default=0)
    goals_total: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    goals_conceded: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    penalty_saved: Mapped[int] = mapped_column(Integer, default=0)
    penalty_missed: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[float] = mapped_column(Float, default=0.0)  # Новое поле для очков

    # Связи
    player: Mapped["Player"] = relationship(back_populates="match_stats")
    match: Mapped["Match"] = relationship(back_populates="player_stats")
    league: Mapped["League"] = relationship()
    team: Mapped["Team"] = relationship()


from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    age: Mapped[int]
    number: Mapped[int]
    position: Mapped[str]
    photo: Mapped[str]
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    market_value: Mapped[int]
    sport: Mapped[int]
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)

    team: Mapped["Team"] = relationship(back_populates="players")
    league: Mapped["League"] = relationship(back_populates="players")
    match_stats: Mapped[list["PlayerMatchStats"]] = relationship(back_populates="player")
    main_squads: Mapped[list["Squad"]] = relationship(
        secondary="squad_players_association", back_populates="players"
    )
    bench_squads: Mapped[list["Squad"]] = relationship(
        secondary="squad_bench_players_association", back_populates="bench_players"
    )

    def __repr__(self):
        return self.name

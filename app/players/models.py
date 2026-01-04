from sqlalchemy import ForeignKey, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

player_squad_tours = Table(
    "squad_tour_players",
    Base.metadata,
    Column("squad_tour_id", Integer, ForeignKey("squad_tours.id"), primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id"), primary_key=True),
    extend_existing=True,
)

player_bench_squad_tours = Table(
    "squad_tour_bench_players",
    Base.metadata,
    Column("squad_tour_id", Integer, ForeignKey("squad_tours.id"), primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id"), primary_key=True),
    extend_existing=True,
)

class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    age: Mapped[int] = mapped_column(nullable=True)
    number: Mapped[int] = mapped_column(nullable=True)
    position: Mapped[str] = mapped_column(nullable=True)
    photo: Mapped[str] = mapped_column(nullable=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    market_value: Mapped[int] = mapped_column(nullable=True)
    sport: Mapped[int] = mapped_column(default=1)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)

    team: Mapped["Team"] = relationship(back_populates="players")
    league: Mapped["League"] = relationship(back_populates="players")
    match_stats: Mapped[list["PlayerMatchStats"]] = relationship(back_populates="player")

    main_squads: Mapped[list["Squad"]] = relationship(
        secondary="squad_players_association",
        back_populates="current_main_players"
    )
    bench_squads: Mapped[list["Squad"]] = relationship(
        secondary="squad_bench_players_association",
        back_populates="current_bench_players"
    )

    squad_tours: Mapped[list["SquadTour"]] = relationship(
        secondary=player_squad_tours,
        back_populates="main_players"
    )
    bench_squad_tours: Mapped[list["SquadTour"]] = relationship(
        secondary=player_bench_squad_tours,
        back_populates="bench_players"
    )

    def __str__(self):
        return self.name
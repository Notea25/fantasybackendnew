from sqlalchemy import Column, ForeignKey, Table, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

squad_players_association = Table(
    "squad_players_association",
    Base.metadata,
    Column("squad_id", ForeignKey("squads.id"), primary_key=True),
    Column("player_id", ForeignKey("players.id"), primary_key=True),
    extend_existing=True,
)

squad_bench_players_association = Table(
    "squad_bench_players_association",
    Base.metadata,
    Column("squad_id", ForeignKey("squads.id"), primary_key=True),
    Column("player_id", ForeignKey("players.id"), primary_key=True),
    extend_existing=True,
)

class Squad(Base):
    __tablename__ = "squads"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    budget: Mapped[int] = mapped_column(default=100_000)
    replacements: Mapped[int] = mapped_column(default=3)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    points: Mapped[int] = mapped_column(default=0)
    user: Mapped["User"] = relationship(back_populates="squads")
    league: Mapped["League"] = relationship(back_populates="squads")
    players: Mapped[list["Player"]] = relationship(
        secondary=squad_players_association, back_populates="main_squads"
    )
    bench_players: Mapped[list["Player"]] = relationship(
        secondary=squad_bench_players_association, back_populates="bench_squads"
    )

    def calculate_points(self):
        main_points = sum(player.points for player in self.players)
        bench_points = sum(player.points for player in self.bench_players) / 2
        self.points = int(main_points + bench_points)

    def __repr__(self):
        return self.name

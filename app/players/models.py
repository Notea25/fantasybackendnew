from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# team_players_association = Table(
#     "team_players_association",
#     Base.metadata,
#     Column("team_id", ForeignKey("teams.id"), primary_key=True),
#     Column("player_id", ForeignKey("players.id"), primary_key=True),
#     extend_existing=True,
# )
#
# team_bench_players_association = Table(
#     "team_bench_players_association",
#     Base.metadata,
#     Column("team_id", ForeignKey("teams.id"), primary_key=True),
#     Column("player_id", ForeignKey("players.id"), primary_key=True),
#     extend_existing=True,
# )


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


    # position: Mapped["Position"] = relationship(back_populates="players")
    # club: Mapped["Club"] = relationship(back_populates="players")
    # sport_type: Mapped["SportType"] = relationship(back_populates="players")
    #
    # main_teams: Mapped[list["Team"]] = relationship(
    #     secondary=team_players_association, back_populates="players"
    # )
    # bench_teams: Mapped[list["Team"]] = relationship(
    #     secondary=team_bench_players_association, back_populates="bench_players"
    # )

    def __repr__(self):
        return self.name

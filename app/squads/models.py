from typing import List, Optional

from sqlalchemy import Column, ForeignKey, Integer, Table, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.player_match_stats.models import PlayerMatchStats


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

squad_tour_players = Table(
    "squad_tour_players",
    Base.metadata,
    Column("squad_tour_id", Integer, ForeignKey("squad_tours.id"), primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id"), primary_key=True),
    extend_existing=True,
)

squad_tour_bench_players = Table(
    "squad_tour_bench_players",
    Base.metadata,
    Column("squad_tour_id", Integer, ForeignKey("squad_tours.id"), primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id"), primary_key=True),
    extend_existing=True,
)

user_league_squads = Table(
    "user_league_squads",
    Base.metadata,
    Column("squad_id", Integer, ForeignKey("squads.id"), primary_key=True),
    Column("user_league_id", Integer, ForeignKey("user_leagues.id"), primary_key=True),
)

commercial_league_squads = Table(
    "commercial_league_squads",
    Base.metadata,
    Column("squad_id", Integer, ForeignKey("squads.id"), primary_key=True),
    Column("commercial_league_id", Integer, ForeignKey("commercial_leagues.id"), primary_key=True),
)

club_league_squads = Table(
    "club_league_squads",
    Base.metadata,
    Column("squad_id", Integer, ForeignKey("squads.id"), primary_key=True),
    Column("club_league_id", Integer, ForeignKey("club_leagues.id"), primary_key=True),
)

class Squad(Base):
    __tablename__ = "squads"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    fav_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    budget: Mapped[int] = mapped_column(default=100_000)
    replacements: Mapped[int] = mapped_column(default=3)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    points: Mapped[int] = mapped_column(default=0)
    current_tour_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tours.id"), nullable=True)
    captain_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"), nullable=True)
    vice_captain_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"), nullable=True)

    fav_team: Mapped["Team"] = relationship(back_populates="squads")
    user: Mapped["User"] = relationship(back_populates="squads")
    league: Mapped["League"] = relationship(back_populates="squads")
    current_main_players: Mapped[List["Player"]] = relationship(
        secondary="squad_players_association",
        back_populates="main_squads",
        lazy="joined",
    )
    current_bench_players: Mapped[List["Player"]] = relationship(
        secondary="squad_bench_players_association",
        back_populates="bench_squads",
        lazy="joined",
    )
    tour_history: Mapped[List["SquadTour"]] = relationship(
        back_populates="squad", cascade="all, delete-orphan"
    )
    used_boosts: Mapped[List["Boost"]] = relationship(back_populates="squad")

    user_leagues: Mapped[List["UserLeague"]] = relationship(
        secondary=user_league_squads, back_populates="squads"
    )
    commercial_leagues: Mapped[List["CommercialLeague"]] = relationship(
        secondary=commercial_league_squads, back_populates="squads"
    )
    club_leagues: Mapped[List["ClubLeague"]] = relationship(
        secondary=club_league_squads, back_populates="squads"
    )

    def __repr__(self):
        return self.name

    @property
    def main_player_ids(self) -> List[int]:
        return [player.id for player in self.current_main_players]

    @property
    def bench_player_ids(self) -> List[int]:
        return [player.id for player in self.current_bench_players]

    def calculate_players_cost(self) -> int:
        return sum(p.market_value for p in self.current_main_players) + sum(
            p.market_value for p in self.current_bench_players
        )

    def validate_players(
        self, main_players: List["Player"], bench_players: List["Player"]
    ) -> None:
        if len(main_players) != 11:
            raise ValueError("Main squad must have exactly 11 players")
        if len(bench_players) != 4:
            raise ValueError("Bench must have exactly 4 players")

        # Check that main squad has at least 1 player of each position
        main_position_counts = {}
        for player in main_players:
            position = player.position
            main_position_counts[position] = main_position_counts.get(position, 0) + 1
        
        # Required: at least 1 Goalkeeper, 1 Defender, 1 Midfielder, 1 Attacker
        if main_position_counts.get("Goalkeeper", 0) < 1:
            raise ValueError("Main squad must have at least 1 Goalkeeper")
        if main_position_counts.get("Defender", 0) < 1:
            raise ValueError("Main squad must have at least 1 Defender")
        if main_position_counts.get("Midfielder", 0) < 1:
            raise ValueError("Main squad must have at least 1 Midfielder")
        if main_position_counts.get("Attacker", 0) < 1 and main_position_counts.get("Forward", 0) < 1:
            raise ValueError("Main squad must have at least 1 Attacker or Forward")

        total_cost = sum(p.market_value for p in main_players + bench_players)
        if total_cost > self.budget:
            raise ValueError("Total players cost exceeds squad budget")

        for player in main_players + bench_players:
            if player.league_id != self.league_id:
                raise ValueError("All players must be from the same league")

        club_counts = {}
        for player in main_players + bench_players:
            club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1
            if club_counts[player.team_id] > 3:
                raise ValueError(
                    "Cannot have more than 3 players from the same club"
                )

    def count_different_players(
        self, new_main_ids: List[int], new_bench_ids: List[int]
    ) -> int:
        current_main_ids = {p.id for p in self.current_main_players}
        current_bench_ids = {p.id for p in self.current_bench_players}
        return len(current_main_ids - set(new_main_ids)) + len(
            current_bench_ids - set(new_bench_ids)
        )

    async def calculate_points(self, session) -> int:
        total_points = 0

        for player in self.current_main_players:
            player_points_stmt = (
                select(func.sum(PlayerMatchStats.points))
                .where(PlayerMatchStats.player_id == player.id)
            )
            player_points_result = await session.execute(player_points_stmt)
            player_points = player_points_result.scalar() or 0
            total_points += player_points

        for player in self.current_bench_players:
            player_points_stmt = (
                select(func.sum(PlayerMatchStats.points))
                .where(PlayerMatchStats.player_id == player.id)
            )
            player_points_result = await session.execute(player_points_stmt)
            player_points = player_points_result.scalar() or 0
            total_points += player_points

        return total_points


class SquadTour(Base):
    __tablename__ = "squad_tours"
    id: Mapped[int] = mapped_column(primary_key=True)
    squad_id: Mapped[int] = mapped_column(
        ForeignKey("squads.id", ondelete="CASCADE"),
        nullable=False,
    )
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id", ondelete="CASCADE"))
    is_current: Mapped[bool] = mapped_column(default=False)
    used_boost: Mapped[Optional[str]] = mapped_column(nullable=True)
    points: Mapped[int] = mapped_column(default=0)
    captain_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"), nullable=True)
    vice_captain_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.id"), nullable=True
    )

    squad: Mapped["Squad"] = relationship(back_populates="tour_history")
    tour: Mapped["Tour"] = relationship(back_populates="squads")
    main_players: Mapped[List["Player"]] = relationship(
        secondary=squad_tour_players, back_populates="squad_tours"
    )
    bench_players: Mapped[List["Player"]] = relationship(
        secondary=squad_tour_bench_players, back_populates="bench_squad_tours"
    )
